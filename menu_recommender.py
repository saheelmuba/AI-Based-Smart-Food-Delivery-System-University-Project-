import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent
INPUT_CSV = ROOT / 'menu_dataset.csv'


def load_menu(csv_path=INPUT_CSV) -> pd.DataFrame:
    """Load the menu dataset and normalize the feature columns."""
    df = pd.read_csv(csv_path, encoding='utf-8')
    df = df.copy()
    df['name'] = df['name'].astype(str).str.strip()
    df['category'] = df['category'].fillna('Unknown').astype(str).str.title()
    df['protein'] = df['protein'].fillna('Balanced').astype(str).str.title()
    df['veg'] = df['veg'].fillna(False).astype(str)
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)
    df['calories'] = pd.to_numeric(df['calories'], errors='coerce').fillna(df['calories'].median())
    df['ai_score'] = pd.to_numeric(df['ai_score'], errors='coerce').fillna(df['ai_score'].mean())
    return df


def build_feature_matrix(menu_df: pd.DataFrame):
    """Build combined feature vectors for content-based recommendations."""
    text_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
    text_matrix = text_vectorizer.fit_transform(menu_df['name'])

    ohe = OneHotEncoder(sparse=False, handle_unknown='ignore')
    cat_matrix = ohe.fit_transform(menu_df[['category', 'protein', 'veg']])

    scaler = StandardScaler()
    num_matrix = scaler.fit_transform(menu_df[['price', 'calories', 'ai_score']])

    feature_matrix = np.hstack([text_matrix.toarray(), cat_matrix, num_matrix])
    return feature_matrix, text_vectorizer, ohe, scaler


def compute_similarity_matrix(feature_matrix: np.ndarray):
    """Compute item-item cosine similarity."""
    return cosine_similarity(feature_matrix, feature_matrix)


def find_item_index(menu_df: pd.DataFrame, query_name: str):
    query = query_name.strip().lower()
    matches = menu_df[menu_df['name'].str.lower() == query]
    if not matches.empty:
        return int(matches.index[0])
    partial_matches = menu_df[menu_df['name'].str.lower().str.contains(query)]
    if not partial_matches.empty:
        return int(partial_matches.index[0])
    return None


def recommend_by_name(menu_df: pd.DataFrame, similarity_matrix: np.ndarray, query_name: str, top_n: int = 5):
    """Return top-N similar menu items for the given item name."""
    idx = find_item_index(menu_df, query_name)
    if idx is None:
        raise ValueError(f'Item not found: {query_name}')

    scores = similarity_matrix[idx]
    order = np.argsort(scores)[::-1]
    order = order[order != idx]
    recommendations = []
    for item_index in order[:top_n]:
        item = menu_df.iloc[item_index].to_dict()
        item['similarity'] = float(scores[item_index])
        recommendations.append(item)
    return recommendations


def recommend_by_id(menu_df: pd.DataFrame, similarity_matrix: np.ndarray, item_id: int, top_n: int = 5):
    """Return top-N similar items by menu item id."""
    row = menu_df[menu_df['id'] == item_id]
    if row.empty:
        raise ValueError(f'Item id not found: {item_id}')
    idx = int(row.index[0])
    scores = similarity_matrix[idx]
    order = np.argsort(scores)[::-1]
    order = order[order != idx]
    recommendations = []
    for item_index in order[:top_n]:
        item = menu_df.iloc[item_index].to_dict()
        item['similarity'] = float(scores[item_index])
        recommendations.append(item)
    return recommendations


def main():
    menu_df = load_menu()
    feature_matrix, _, _, _ = build_feature_matrix(menu_df)
    similarity_matrix = compute_similarity_matrix(feature_matrix)

    queries = [
        'Rice and Veg Curry',
        'Chicken Briyani',
        'Mango'
    ]

    for query in queries:
        print(f'\nRecommendations for: {query}')
        try:
            recs = recommend_by_name(menu_df, similarity_matrix, query, top_n=5)
            for i, rec in enumerate(recs, start=1):
                print(f"{i}. {rec['name']} ({rec['category']}) - Rs.{rec['price']} - similarity={rec['similarity']:.3f}")
        except ValueError as exc:
            print(str(exc))


if __name__ == '__main__':
    main()
