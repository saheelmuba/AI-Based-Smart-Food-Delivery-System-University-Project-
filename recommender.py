from models import FoodOrder, Recommendation, db
from collections import Counter


def recommend_for_user(user_id, top_n=5):
    # Simple popularity-based recommender using recent orders
    orders = FoodOrder.query.order_by(FoodOrder.created_at.desc()).limit(500).all()
    item_counter = Counter()
    for order in orders:
        items = order.items or []
        for it in items:
            name = it.get('name') if isinstance(it, dict) else str(it)
            item_counter[name.lower()] += 1

    most_common = [name for name, _ in item_counter.most_common(top_n)]
    # Persist recommendations for auditing
    for name in most_common:
        rec = Recommendation(user_id=user_id, reference_id=None, reason=f'popular:{name}')
        db.session.add(rec)
    db.session.commit()
    return most_common
