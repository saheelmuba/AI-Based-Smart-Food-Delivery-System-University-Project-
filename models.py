from datetime import datetime
from database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(40), default="patient", nullable=False)
    contact_phone = db.Column(db.String(40), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor_profile = db.relationship("DoctorProfile", back_populates="user", uselist=False)
    emergency_alerts = db.relationship("EmergencyAlert", back_populates="patient", cascade="all, delete-orphan")
    appointments_as_patient = db.relationship("Appointment", back_populates="patient", foreign_keys="Appointment.patient_id", cascade="all, delete-orphan")
    appointments_as_doctor = db.relationship("Appointment", back_populates="doctor", foreign_keys="Appointment.doctor_id", cascade="all, delete-orphan")
    medical_records_as_patient = db.relationship("MedicalRecord", back_populates="patient", foreign_keys="MedicalRecord.patient_id", cascade="all, delete-orphan")
    medical_records_as_doctor = db.relationship("MedicalRecord", back_populates="doctor", foreign_keys="MedicalRecord.doctor_id", cascade="all, delete-orphan")
    prescriptions_as_patient = db.relationship("Prescription", back_populates="patient", foreign_keys="Prescription.patient_id", cascade="all, delete-orphan")
    prescriptions_as_doctor = db.relationship("Prescription", back_populates="doctor", foreign_keys="Prescription.doctor_id", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    chat_logs = db.relationship("ChatLog", back_populates="user", cascade="all, delete-orphan")
    voice_logs = db.relationship("VoiceLog", back_populates="user", cascade="all, delete-orphan")
    image_analysis_logs = db.relationship("ImageAnalysisLog", backref="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "contact_phone": self.contact_phone,
            "created_at": self.created_at.isoformat(),
        }


class DoctorProfile(db.Model):
    __tablename__ = "doctor_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    specialty = db.Column(db.String(120), nullable=False)
    clinic_address = db.Column(db.String(260), nullable=True)
    schedule = db.Column(db.String(240), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="doctor_profile")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "specialty": self.specialty,
            "clinic_address": self.clinic_address,
            "schedule": self.schedule,
            "bio": self.bio,
            "created_at": self.created_at.isoformat(),
        }


class EmergencyAlert(db.Model):
    __tablename__ = "emergency_alerts"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    issue = db.Column(db.String(260), nullable=False)
    location = db.Column(db.String(260), nullable=True)
    status = db.Column(db.String(80), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("User", back_populates="emergency_alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "issue": self.issue,
            "location": self.location,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(80), default="scheduled", nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("User", back_populates="appointments_as_patient", foreign_keys=[patient_id])
    doctor = db.relationship("User", back_populates="appointments_as_doctor", foreign_keys=[doctor_id])

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "scheduled_at": self.scheduled_at.isoformat(),
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class MedicalRecord(db.Model):
    __tablename__ = "medical_records"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    record_type = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(220), nullable=False)
    description = db.Column(db.Text, nullable=True)
    findings = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("User", back_populates="medical_records_as_patient", foreign_keys=[patient_id])
    doctor = db.relationship("User", back_populates="medical_records_as_doctor", foreign_keys=[doctor_id])

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "record_type": self.record_type,
            "title": self.title,
            "description": self.description,
            "findings": self.findings,
            "created_at": self.created_at.isoformat(),
        }


class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    medication = db.Column(db.String(220), nullable=False)
    dosage = db.Column(db.String(120), nullable=False)
    frequency = db.Column(db.String(120), nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("User", back_populates="prescriptions_as_patient", foreign_keys=[patient_id])
    doctor = db.relationship("User", back_populates="prescriptions_as_doctor", foreign_keys=[doctor_id])

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "medication": self.medication,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "instructions": self.instructions,
            "created_at": self.created_at.isoformat(),
        }


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "reference_id": self.reference_id,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    channel = db.Column(db.String(80), nullable=False)
    subject = db.Column(db.String(220), nullable=False)
    content = db.Column(db.Text, nullable=False)
    delivered = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "channel": self.channel,
            "subject": self.subject,
            "content": self.content,
            "delivered": self.delivered,
            "created_at": self.created_at.isoformat(),
        }


class ChatLog(db.Model):
    __tablename__ = "chat_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    session_id = db.Column(db.String(120), nullable=True, index=True)
    role = db.Column(db.String(40), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="chat_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "role": self.role,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
        }


class VoiceLog(db.Model):
    __tablename__ = "voice_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    transcript = db.Column(db.Text, nullable=False)
    command = db.Column(db.String(160), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="voice_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "transcript": self.transcript,
            "command": self.command,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }


class ImageAnalysisLog(db.Model):
    __tablename__ = "image_analysis_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    image_path = db.Column(db.String(300), nullable=False)
    labels = db.Column(db.String(300), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    image_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_path": self.image_path,
            "labels": self.labels.split(",") if self.labels else [],
            "confidence": self.confidence,
            "metadata": self.image_metadata,
            "created_at": self.created_at.isoformat(),
        }


class AnalyticsEvent(db.Model):
    __tablename__ = "analytics_events"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(120), nullable=False)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


class FoodOrder(db.Model):
    __tablename__ = "food_orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(140), nullable=False)
    customer_phone = db.Column(db.String(40), nullable=True)
    delivery_address = db.Column(db.String(260), nullable=False)
    items = db.Column(db.JSON, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(80), default="preparing", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "delivery_address": self.delivery_address,
            "items": self.items,
            "total": self.total,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


