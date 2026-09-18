from datetime import datetime
from models import Recommendation, db


SUGGESTION_MAP = {
    "fever": ["Drink plenty of fluids", "Monitor temperature every 4 hours", "Book an appointment if the fever persists"],
    "cough": ["Stay hydrated", "Use throat lozenges", "Consider a telehealth visit for persistent coughing"],
    "headache": ["Rest in a quiet room", "Stay hydrated", "Schedule a doctor review if pain continues"],
}


def recommend_care_path(symptoms):
    symptoms_text = (symptoms or "").lower()
    recommendations = []
    for keyword, advice in SUGGESTION_MAP.items():
        if keyword in symptoms_text:
            recommendations.extend(advice)
    if not recommendations:
        recommendations.append("Speak with a physician for a personalized care plan.")
    return recommendations


def save_recommendation(user_id, content, reason):
    entry = Recommendation(user_id=user_id, reference_id=None, reason=reason)
    db.session.add(entry)
    db.session.commit()
    return entry
