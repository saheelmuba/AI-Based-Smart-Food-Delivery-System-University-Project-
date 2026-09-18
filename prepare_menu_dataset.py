import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
CANTEEN_CSV = ROOT / 'canteen.csv'
JUICE_CSV = ROOT / 'Fresh_Juice_Product_Prices.csv'
OUTPUT_JSON = ROOT / 'menu_dataset.json'
OUTPUT_CSV = ROOT / 'menu_dataset.csv'
OUTPUT_JS = ROOT / 'menu_dataset.js'
OUTPUT_PY = ROOT / 'menu_dataset.py'

CATEGORY_MAP = {
    'breakfast': 'Breakfast',
    'lunch': 'Lunch',
    'dinner': 'Dinner',
    'snack': 'Snack',
    'beverage': 'Beverage',
    'drinks': 'Beverage',
    'dessert': 'Dessert',
}

VEG_KEYWORDS = [
    'veg', 'vegetable', 'salad', 'juice', 'fruit', 'tea', 'lassi', 'milo', 'cheese',
    'bread', 'sambol', 'idli', 'dosa', 'pittu', 'rice', 'noodles', 'macaroni',
    'pancake', 'rotti', 'hoppers', 'sambal', 'coconut', 'plain', 'milk', 'soy',
    'banana', 'pineapple', 'orange', 'watermelon', 'avocado', 'mango'
]

NON_VEG_KEYWORDS = [
    'chicken', 'beef', 'fish', 'mutton', 'prawn', 'seafood', 'meat', 'pork',
    'turkey', 'egg', 'shrimp', 'crab', 'lobster'
]

EMOJI_MAP = {
    'Breakfast': '🌅',
    'Lunch': '🍽️',
    'Dinner': '🌙',
    'Snack': '🧆',
    'Beverage': '🥤',
    'Dessert': '🍦',
    'Unknown': '🍴',
}

CALORIE_MAP = {
    'Breakfast': 520,
    'Lunch': 620,
    'Dinner': 650,
    'Snack': 320,
    'Beverage': 180,
    'Dessert': 400,
    'Unknown': 420,
}


def clean_price(value):
    if pd.isna(value):
        return None
    text = str(value).replace('\ufeff', '').strip().replace('Rs.', '').replace('Rs', '')
    text = re.sub(r'[^0-9]', ' ', text).strip()
    match = re.search(r'(\d+)', text)
    if not match:
        return None
    return int(match.group(1))


def normalize_label(label):
    if label is None:
        return None
    text = re.sub(r'\s+', ' ', str(label).strip())
    if not text:
        return None
    return text.rstrip(':').strip()


def detect_category(label):
    label = normalize_label(label)
    if not label:
        return None
    lower = label.lower()
    return CATEGORY_MAP.get(lower)


def infer_veg(name):
    if not name or not isinstance(name, str):
        return None
    lower = name.lower()
    if any(word in lower for word in NON_VEG_KEYWORDS):
        return False
    if any(word in lower for word in VEG_KEYWORDS):
        return True
    return None


def infer_emoji(name, category):
    lower = name.lower()
    if 'chicken' in lower or 'briyani' in lower or 'kottu' in lower:
        return '🍗'
    if 'beef' in lower or 'breef' in lower or 'burger' in lower:
        return '🥩'
    if 'fish' in lower or 'seafood' in lower:
        return '🐟'
    if 'egg' in lower or 'omelette' in lower:
        return '🥚'
    if 'juice' in lower or 'lemon' in lower or 'mango' in lower or 'orange' in lower:
        return '🥤'
    if 'rice' in lower or 'curry' in lower:
        return '🍛'
    if 'rotti' in lower or 'bread' in lower or 'sandwich' in lower:
        return '🍞'
    if 'samosa' in lower or 'cutlet' in lower or 'roll' in lower:
        return '🥟'
    return EMOJI_MAP.get(category, '🍴')


def infer_protein(name):
    lower = name.lower()
    if any(k in lower for k in ['chicken', 'beef', 'fish', 'mutton', 'prawn', 'egg', 'shrimp', 'crab', 'lobster']):
        return 'High Protein'
    if any(k in lower for k in ['veg', 'vegetable', 'fruit', 'juice', 'salad', 'bread', 'noodles', 'rice', 'dosa', 'idli']):
        return 'Vegetarian'
    return 'Balanced'


def infer_calories(category):
    return CALORIE_MAP.get(category, CALORIE_MAP['Unknown'])


def infer_ai_score(name):
    if not name:
        return 72
    return 70 + (sum(ord(ch) for ch in name) % 21)


def load_canteen_menu():
    df = pd.read_csv(CANTEEN_CSV, header=None, dtype=str)
    df = df.iloc[:, [6, 14]]
    df.columns = ['name', 'price']

    rows = []
    current_cat = 'Unknown'
    for _, row in df.iterrows():
        name = normalize_label(row['name'])
        price = normalize_label(row['price'])

        if not name and not price:
            continue

        category = detect_category(name)
        if category:
            current_cat = category
            continue

        if name and name.lower().startswith('kalith lanka products'):
            continue

        if not name or not price:
            continue

        cleaned_price = clean_price(price)
        if cleaned_price is None:
            continue

        rows.append(
            {
                'name': name,
                'price': cleaned_price,
                'category': current_cat,
                'veg': infer_veg(name),
                'emoji': infer_emoji(name, current_cat),
                'protein': infer_protein(name),
                'calories': infer_calories(current_cat),
                'ai_score': infer_ai_score(name),
                'source': 'canteen',
                'raw_price': price,
            }
        )

    return rows


def load_juice_menu():
    df = pd.read_csv(JUICE_CSV, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: 'name', df.columns[1]: 'price'})

    items = []
    for _, row in df.iterrows():
        name = normalize_label(row['name'])
        price = normalize_label(row['price'])
        if not name or not price:
            continue

        cleaned_price = clean_price(price)
        if cleaned_price is None:
            continue

        items.append(
            {
                'name': name,
                'price': cleaned_price,
                'category': 'Beverage',
                'veg': True,
                'emoji': infer_emoji(name, 'Beverage'),
                'protein': infer_protein(name),
                'calories': infer_calories('Beverage'),
                'ai_score': infer_ai_score(name),
                'source': 'juice',
                'raw_price': price,
            }
        )
    return items


def build_menu_dataset():
    canteen_items = load_canteen_menu()
    juice_items = load_juice_menu()
    menu = canteen_items + juice_items
    for idx, item in enumerate(menu, start=1):
        item['id'] = idx
    return menu


def save_menu(menu):
    with OUTPUT_JSON.open('w', encoding='utf-8') as fp:
        json.dump(menu, fp, indent=2, ensure_ascii=False)

    df = pd.DataFrame(menu)
    df.to_csv(OUTPUT_CSV, index=False)

    with OUTPUT_JS.open('w', encoding='utf-8') as fp:
        fp.write('const MENU = ')
        json.dump(menu, fp, indent=2, ensure_ascii=False)
        fp.write(';\n')

    with OUTPUT_PY.open('w', encoding='utf-8') as fp:
        fp.write('# Menu dataset exported from prepare_menu_dataset.py\n')
        fp.write('MENU = ')
        fp.write(repr(menu))
        fp.write('\n')


def main():
    menu = build_menu_dataset()
    save_menu(menu)
    print(f'Saved {len(menu)} menu items to:')
    print(f' - {OUTPUT_JSON}')
    print(f' - {OUTPUT_CSV}')
    print(f' - {OUTPUT_JS}')
    print(f' - {OUTPUT_PY}')


if __name__ == '__main__':
    main()
