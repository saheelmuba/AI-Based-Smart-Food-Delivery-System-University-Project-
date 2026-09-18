from datetime import datetime
from sqlalchemy import func
from database import db
from models import Order, OrderItem, MenuItem, VoiceLog, ChatLog, ImageAnalysisLog


def get_dashboard_metrics():
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.coalesce(func.sum(Order.grand_total), 0.0)).scalar() or 0.0
    most_ordered = (
        db.session.query(
            MenuItem.name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label('quantity')
        )
        .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
        .group_by(MenuItem.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    return {
        'total_orders': total_orders,
        'total_revenue': round(total_revenue, 2),
        'top_items': [{'name': name, 'quantity': int(qty)} for name, qty in most_ordered],
        'voice_sessions': VoiceLog.query.count(),
        'chat_sessions': ChatLog.query.count(),
        'image_scans': ImageAnalysisLog.query.count(),
        'last_updated': datetime.utcnow().isoformat()
    }
