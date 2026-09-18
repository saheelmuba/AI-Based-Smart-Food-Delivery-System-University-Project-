from sqlalchemy import func
from database import db
from models import (
    User,
    Appointment,
    MedicalRecord,
    EmergencyAlert,
    Notification,
    AnalyticsEvent,
    ChatLog,
    ImageAnalysisLog,
)

CARE_SERVICES = [
    {
        "title": "Primary Care Consultation",
        "description": "Routine check-ups, preventive screenings, and chronic condition management.",
        "category": "General Medicine",
    },
    {
        "title": "Specialist Referral",
        "description": "Cardiology, endocrinology, orthopedics, and other specialist pathways.",
        "category": "Specialist Care",
    },
    {
        "title": "Telehealth Visit",
        "description": "Remote consultations with licensed physicians through secure video sessions.",
        "category": "Virtual Care",
    },
    {
        "title": "Lab & Imaging Review",
        "description": "Upload and review lab results, X-rays, and diagnostic imaging with AI support.",
        "category": "Diagnostics",
    },
    {
        "title": "Emergency Alert Triage",
        "description": "Submit urgent symptoms and notify care teams for rapid response coordination.",
        "category": "Emergency",
    },
    {
        "title": "Prescription Management",
        "description": "Track medications, dosage schedules, and refill reminders in one place.",
        "category": "Pharmacy",
    },
]


def compile_dashboard_metrics():
    patient_count = int(db.session.query(func.count(User.id)).filter_by(role="patient").scalar() or 0)
    doctor_count = int(db.session.query(func.count(User.id)).filter_by(role="doctor").scalar() or 0)
    appointment_count = int(db.session.query(func.count(Appointment.id)).scalar() or 0)
    medical_record_count = int(db.session.query(func.count(MedicalRecord.id)).scalar() or 0)
    emergency_count = int(db.session.query(func.count(EmergencyAlert.id)).scalar() or 0)
    notification_count = int(db.session.query(func.count(Notification.id)).scalar() or 0)
    active_alerts = int(
        db.session.query(func.count(EmergencyAlert.id)).filter_by(status="pending").scalar() or 0
    )
    assistant_usage = int(db.session.query(func.count(ChatLog.id)).filter_by(role="assistant").scalar() or 0)
    image_usage = int(db.session.query(func.count(ImageAnalysisLog.id)).scalar() or 0)

    workflows = [
        {
            "title": "Pending Emergency Alerts",
            "value": active_alerts,
            "detail": "Alerts awaiting clinical review.",
        },
        {
            "title": "Scheduled Appointments",
            "value": appointment_count,
            "detail": "Upcoming and active patient visits.",
        },
        {
            "title": "Medical Records",
            "value": medical_record_count,
            "detail": "Clinical documents stored in the platform.",
        },
        {
            "title": "Care Notifications",
            "value": notification_count,
            "detail": "Messages sent to patients and providers.",
        },
    ]

    trends = [
        {"label": "Active Patients", "value": patient_count},
        {"label": "Registered Doctors", "value": doctor_count},
        {"label": "Emergency Cases", "value": emergency_count},
        {"label": "Assistant Conversations", "value": assistant_usage},
    ]

    return {
        "patient_count": patient_count,
        "doctor_count": doctor_count,
        "appointment_count": appointment_count,
        "medical_record_count": medical_record_count,
        "emergency_alert_count": emergency_count,
        "active_alerts": active_alerts,
        "notification_count": notification_count,
        "assistant_usage": assistant_usage,
        "image_usage": image_usage,
        "workflows": workflows,
        "trends": trends,
    }


def list_recent_appointments(limit=12):
    appointments = (
        Appointment.query.order_by(Appointment.scheduled_at.desc()).limit(limit).all()
    )
    return [appointment.to_dict() for appointment in appointments]


def list_care_services():
    return CARE_SERVICES


def record_analytics_event(event_type, payload=None):
    event = AnalyticsEvent(event_type=event_type, payload=payload or {})
    db.session.add(event)
    db.session.commit()
    return event
