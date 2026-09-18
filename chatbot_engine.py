import random
from models import ChatLog, db

FAQ_PAIRS = [
    {
        "question": "how long does delivery take",
        "answer": "Most orders arrive in 30-45 minutes depending on your location and restaurant load.",
    },
    {
        "question": "what are your delivery hours",
        "answer": "We deliver daily from 10:00 AM to 11:00 PM.",
    },
    {
        "question": "how do i track my order",
        "answer": "Open the Orders page to see your order status and estimated delivery time.",
    },
    {
        "question": "do you have vegetarian options",
        "answer": "Yes. Check the Menu page for salads, pasta, and other vegetarian dishes.",
    },
]


def create_faq_response(message):
    query = message.lower().strip()
    for faq in FAQ_PAIRS:
        if faq["question"] in query:
            return faq["answer"]
    return None


def generate_assistant_response(user_id, session_id, message):
    ChatLog.query.filter_by(session_id=session_id).order_by(ChatLog.created_at.desc()).limit(5).all()
    faq_answer = create_faq_response(message)

    if faq_answer:
        response = faq_answer
    elif any(term in message.lower() for term in ["pizza", "burger", "pasta", "menu"]):
        response = "Browse the Menu page to add items to your cart. Popular picks include Margherita Pizza and Grilled Chicken Burger."
    elif any(term in message.lower() for term in ["order", "delivery", "track"]):
        response = "Place your order from the Cart page, then track it on the Orders page."
    elif any(term in message.lower() for term in ["price", "cost", "cheap", "deal"]):
        response = "Menu prices start from $3.99 for drinks. Add items to your cart to see the total before checkout."
    else:
        response = random.choice(
            [
                "Tell me what you are craving and I can suggest dishes from our menu.",
                "I can help you browse the menu, build your cart, or track a delivery.",
                "Ask me about delivery time, menu items, order tracking, or payment options.",
            ]
        )

    db.session.add(ChatLog(user_id=user_id, session_id=session_id, role="user", message=message))
    db.session.add(ChatLog(user_id=user_id, session_id=session_id, role="assistant", message=response))
    db.session.commit()
    return response
