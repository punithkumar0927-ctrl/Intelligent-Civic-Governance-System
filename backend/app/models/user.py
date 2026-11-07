from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    username    = Column(String(50),  unique=True, index=True, nullable=False)
    email       = Column(String(120), unique=True, index=True, nullable=False)
    full_name   = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    phone       = Column(String(15),  nullable=True)
    role        = Column(String(20),  default="citizen", nullable=False)
    jurisdiction_boundary_id = Column(Integer, nullable=True)
    is_active   = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)   # email verified
    email_verification_token = Column(String(128), nullable=True, index=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String(128), nullable=True, index=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    refresh_token_hash = Column(String(128), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    issues = relationship(
        "Issue",
        back_populates="reporter",
        lazy="dynamic",
        foreign_keys="Issue.reporter_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
