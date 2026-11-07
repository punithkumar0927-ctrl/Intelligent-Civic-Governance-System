"""Civic reports and jurisdiction records.

Boundary names and official contacts are stored only when an administrator imports them.
Nothing in this module seeds a Gram Panchayat, phone number, or government acknowledgement.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from app.database import Base


class IssueCategory(Base):
    __tablename__ = "issue_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)


class AdministrativeBoundary(Base):
    __tablename__ = "administrative_boundaries"
    id = Column(Integer, primary_key=True)
    level = Column(String(40), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("administrative_boundaries.id"), nullable=True)
    source = Column(String(200), nullable=False)
    lgd_code = Column(String(40), nullable=True)
    geometry_json = Column(Text, nullable=False)
    verified = Column(Boolean, nullable=False, default=False)


class GramPanchayat(Base):
    __tablename__ = "gram_panchayats"
    id = Column(Integer, primary_key=True)
    boundary_id = Column(Integer, ForeignKey("administrative_boundaries.id"), unique=True, nullable=False)
    name = Column(String(200), nullable=False)


class TalukPanchayat(Base):
    __tablename__ = "taluk_panchayats"
    id = Column(Integer, primary_key=True)
    boundary_id = Column(Integer, ForeignKey("administrative_boundaries.id"), unique=True, nullable=False)
    name = Column(String(200), nullable=False)


class ZillaPanchayat(Base):
    __tablename__ = "zilla_panchayats"
    id = Column(Integer, primary_key=True)
    boundary_id = Column(Integer, ForeignKey("administrative_boundaries.id"), unique=True, nullable=False)
    name = Column(String(200), nullable=False)


class UrbanLocalBody(Base):
    __tablename__ = "urban_local_bodies"
    id = Column(Integer, primary_key=True)
    boundary_id = Column(Integer, ForeignKey("administrative_boundaries.id"), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    body_type = Column(String(40), nullable=False, default="unspecified")


class AuthorityDirectory(Base):
    __tablename__ = "authority_directory"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    department = Column(String(120), nullable=False)
    boundary_id = Column(Integer, ForeignKey("administrative_boundaries.id"), nullable=True)
    email = Column(String(160), nullable=True)
    phone = Column(String(20), nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)


class RoutingRule(Base):
    __tablename__ = "routing_rules"
    id = Column(Integer, primary_key=True)
    category = Column(String(120), nullable=False)
    boundary_level = Column(String(40), nullable=False)
    authority_id = Column(Integer, ForeignKey("authority_directory.id"), nullable=False)
    escalation_authority_id = Column(Integer, ForeignKey("authority_directory.id"), nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)


class CitizenReport(Base):
    __tablename__ = "citizen_reports"
    id = Column(Integer, primary_key=True)
    reference = Column(String(40), unique=True, nullable=False, index=True)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(120), nullable=False)
    ai_status = Column(String(40), nullable=False, default="not_run")
    ai_label = Column(String(120), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_severity = Column(String(20), nullable=True)
    ai_risk_note = Column(Text, nullable=True)
    ai_description = Column(Text, nullable=True)
    possible_duplicate_of = Column(Integer, ForeignKey("citizen_reports.id"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_accuracy = Column(Float, nullable=True)
    citizen_district = Column(String(120), nullable=True)
    citizen_taluk = Column(String(120), nullable=True)
    citizen_village = Column(String(120), nullable=True)
    citizen_gram_panchayat = Column(String(200), nullable=True)
    jurisdiction_status = Column(String(40), nullable=False, default="pending_verification")
    boundary_id = Column(Integer, ForeignKey("administrative_boundaries.id"), nullable=True)
    verified_state = Column(String(80), nullable=True)
    verified_district = Column(String(120), nullable=True)
    verified_taluk = Column(String(120), nullable=True)
    verified_village = Column(String(120), nullable=True)
    verified_gram_panchayat = Column(String(200), nullable=True)
    verified_ulb = Column(String(200), nullable=True)
    authority_id = Column(Integer, ForeignKey("authority_directory.id"), nullable=True)
    assigned_official_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(60), nullable=False)
    official_reference = Column(String(80), nullable=True)
    government_delivery = Column(String(40), nullable=False, default="not_sent")
    notify_consent = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportMedia(Base):
    __tablename__ = "report_media"
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("citizen_reports.id"), nullable=False, index=True)
    stored_name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(80), nullable=False)
    media_kind = Column(String(20), nullable=False)
    phash = Column(String(64), nullable=True)


class ReportAssignment(Base):
    __tablename__ = "report_assignments"
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("citizen_reports.id"), nullable=False)
    official_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportStatusHistory(Base):
    __tablename__ = "report_status_history"
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("citizen_reports.id"), nullable=False, index=True)
    status = Column(String(60), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    source = Column(String(40), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OfficialActionRecord(Base):
    __tablename__ = "official_action_records"
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("citizen_reports.id"), nullable=False)
    official_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(40), nullable=False)
    note = Column(Text, nullable=True)
    media_id = Column(Integer, ForeignKey("report_media.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey("citizen_reports.id"), nullable=True)
    kind = Column(String(40), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CitizenFeedback(Base):
    __tablename__ = "citizen_feedback"
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("citizen_reports.id"), nullable=False)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    satisfied = Column(Boolean, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
