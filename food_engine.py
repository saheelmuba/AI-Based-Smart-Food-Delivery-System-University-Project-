import json
import os
from sqlalchemy import func
from database import db
from models import FoodOrder, ChatLog

MENU_PATH = os.path.join(os.getcwd(), "datasets", "menu.json")


def load_menu_items():
    if not os.path.exists(MENU_PATH):
        return []
    with open(MENU_PATH, "r", encoding="utf-8") as reader:
        return json.load(reader)


def get_menu_item(item_id):
    for item in load_menu_items():
        if item["id"] == item_id:
            return item
    return None


def calculate_order_total(items):
    total = 0.0
    for entry in items:
        menu_item = get_menu_item(entry.get("id"))
        if not menu_item:
            continue
        quantity = max(int(entry.get("quantity", 1)), 1)
        total += float(menu_item["price"]) * quantity
    return round(total, 2)


def normalize_order_items(items):
    normalized = []
    for entry in items or []:
        menu_item = get_menu_item(entry.get("id"))
        if not menu_item:
            continue
        quantity = max(int(entry.get("quantity", 1)), 1)
        normalized.append(
            {
                "id": menu_item["id"],
                "name": menu_item["name"],
                "price": menu_item["price"],
                "quantity": quantity,
            }
        )
    return normalized


def create_food_order(customer_name, customer_phone, delivery_address, items):
    normalized_items = normalize_order_items(items)
    if not normalized_items:
        return None, "Add at least one valid menu item to your order."

    order = FoodOrder(
        customer_name=customer_name.strip(),
        customer_phone=(customer_phone or "").strip(),
        delivery_address=delivery_address.strip(),
        items=normalized_items,
        total=calculate_order_total(normalized_items),
        status="preparing",
    )
    db.session.add(order)
    db.session.commit()
    return order, None


def list_food_orders(limit=20):
    orders = FoodOrder.query.order_by(FoodOrder.created_at.desc()).limit(limit).all()
    return [order.to_dict() for order in orders]


def compile_food_dashboard_metrics():
    menu_items = load_menu_items()
    order_count = int(db.session.query(func.count(FoodOrder.id)).scalar() or 0)
    revenue = float(db.session.query(func.coalesce(func.sum(FoodOrder.total), 0)).scalar() or 0)
    pending_orders = int(
        db.session.query(func.count(FoodOrder.id)).filter(FoodOrder.status.in_(["pending", "preparing"])).scalar()
        or 0
    )
    delivered_orders = int(
        db.session.query(func.count(FoodOrder.id)).filter_by(status="delivered").scalar() or 0
    )
    assistant_usage = int(db.session.query(func.count(ChatLog.id)).filter_by(role="assistant").scalar() or 0)

    category_counts = {}
    for item in menu_items:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1

    workflows = [
        {"title": "Active Orders", "value": pending_orders, "detail": "Orders being prepared for delivery."},
        {"title": "Delivered Today", "value": delivered_orders, "detail": "Completed deliveries on the platform."},
        {"title": "Menu Items", "value": len(menu_items), "detail": "Dishes available to order right now."},
        {"title": "Total Orders", "value": order_count, "detail": "All orders placed through the app."},
    ]

    trends = [
        {"label": "Total Revenue", "value": f"${revenue:.2f}"},
        {"label": "Pizza Items", "value": category_counts.get("Pizza", 0)},
        {"label": "Burger Items", "value": category_counts.get("Burgers", 0)},
        {"label": "Assistant Chats", "value": assistant_usage},
    ]

    return {
        "menu_item_count": len(menu_items),
        "order_count": order_count,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "revenue": revenue,
        "assistant_usage": assistant_usage,
        "workflows": workflows,
        "trends": trends,
    }
