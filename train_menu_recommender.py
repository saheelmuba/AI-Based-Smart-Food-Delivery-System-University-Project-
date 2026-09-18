import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
INPUT_CSV = ROOT / 'menu_dataset.csv'
OUTPUT_MODEL = ROOT / 'menu_recommender.pkl'


def load_menu(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding='utf-8')
    df = df.copy()
    df['name'] = df['name'].astype(str).str.strip()
    df['category'] = df['category'].fillna('Unknown').astype(str).str.title()
    df['protein'] = df['protein'].fillna('Balanced').astype(str).str.title()
    veg_column = df['veg'].copy()
    veg_column[veg_column.isna()] = False
    df['veg'] = veg_column.astype(str)
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)
    df['calories'] = pd.to_numeric(df['calories'], errors='coerce').fillna(df['calories'].median())
    df['ai_score'] = pd.to_numeric(df['ai_score'], errors='coerce').fillna(df['ai_score'].mean())
    return df


def build_recommender_pipeline() -> Pipeline:
    text_transformer = TfidfVectorizer(ngram_range=(1, 2), max_features=600, stop_words='english')

    categorical_transformer = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    numeric_transformer = StandardScaler()

    preprocessor = ColumnTransformer(
        transformers=[
            ('text', text_transformer, 'name'),
            ('cat', categorical_transformer, ['category', 'protein', 'veg']),
            ('num', numeric_transformer, ['price', 'calories', 'ai_score']),
        ],
        remainder='drop',
        sparse_threshold=0.0,
    )

    recommender = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=11, n_jobs=-1)

    pipeline = Pipeline(
        steps=[
            ('preprocessor', preprocessor),
            ('neighbors', recommender),
        ]
    )
    return pipeline


def evaluate_category_consistency(df: pd.DataFrame, pipeline: Pipeline, top_n: int = 5) -> float:
    feature_matrix = pipeline.named_steps['preprocessor'].transform(df)
    distances, indices = pipeline.named_steps['neighbors'].kneighbors(feature_matrix, n_neighbors=top_n + 1)

    category_matches = []
    for item_idx, neighbors in enumerate(indices):
        item_category = df.iloc[item_idx]['category']
        neighbor_indices = [idx for idx in neighbors if idx != item_idx][:top_n]
        matched = sum(1 for idx in neighbor_indices if df.iloc[idx]['category'] == item_category)
        category_matches.append(matched / float(top_n))

    return float(np.mean(category_matches))


def train():
    df = load_menu(INPUT_CSV)
    pipeline = build_recommender_pipeline()
    pipeline.fit(df)

    consistency = evaluate_category_consistency(df, pipeline, top_n=5)
    print(f'Trained NearestNeighbors recommender on {len(df)} items.')
    print(f'Category consistency score (top-5 neighbors): {consistency:.4f}')

    model_data = {
        'pipeline': pipeline,
        'items': df[['id', 'name', 'category', 'price', 'veg', 'protein', 'calories', 'ai_score', 'source', 'raw_price']].reset_index(drop=True),
    }
    joblib.dump(model_data, OUTPUT_MODEL, compress=3)
    print(f'Saved trained model to: {OUTPUT_MODEL}')
    return model_data


def load_trained_model(model_path: Path = OUTPUT_MODEL):
    return joblib.load(model_path)


def recommend_by_name(name: str, model_data: dict, top_n: int = 5):
    df = model_data['items']
    pipeline = model_data['pipeline']
    query = name.strip().lower()
    row = df[df['name'].str.lower() == query]
    if row.empty:
        row = df[df['name'].str.lower().str.contains(query)]
    if row.empty:
        raise ValueError(f'Unable to find menu item matching "{name}".')

    idx = int(row.index[0])
    feature_matrix = pipeline.named_steps['preprocessor'].transform(df)
    distances, indices = pipeline.named_steps['neighbors'].kneighbors(feature_matrix[idx:idx + 1], n_neighbors=top_n + 1)
    result = []
    for neighbor_idx, distance in zip(indices[0], distances[0]):
        if neighbor_idx == idx:
            continue
        item = df.iloc[neighbor_idx].to_dict()
        item['similarity'] = float(1.0 - distance)
        result.append(item)
        if len(result) >= top_n:
            break
    return result


def main():
    trained = train()
    print('\nSample inference results:')
    for query in ['Rice and Veg Curry', 'Chicken Briyani', 'Mango']:
        try:
            recs = recommend_by_name(query, trained, top_n=5)
            print(f'\nRecommendations for: {query}')
            for position, item in enumerate(recs, start=1):
                print(f"{position}. {item['name']} ({item['category']}) - Rs.{item['price']} - similarity={item['similarity']:.3f}")
        except ValueError as exc:
            print(str(exc))


if __name__ == '__main__':
    main()
