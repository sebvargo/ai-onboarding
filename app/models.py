# app/models.py
import sqlalchemy as sa
import sqlalchemy.orm as orm
import uuid

from app import db
from sqlalchemy import Column, String, Integer, ForeignKey, Text, TIMESTAMP, Enum, Boolean, DateTime, func 
from sqlalchemy.dialects.postgresql import UUID as sa_UUID, JSONB
from typing import Optional


class User(db.Model):
    uid: orm.Mapped[uuid.UUID] = orm.mapped_column(sa_UUID, unique=True, primary_key=True, default=uuid.uuid4,server_default=sa.text("uuid_generate_v4()"),)
    firstname: orm.Mapped[Optional[str]] = orm.mapped_column(Text)
    lastname: orm.Mapped[Optional[str]] = orm.mapped_column(Text)
    title: orm.Mapped[Optional[str]] = orm.mapped_column(Text)
    company: orm.Mapped[Optional[str]] = orm.mapped_column(Text)
    company_size: orm.Mapped[Optional[str]] = orm.mapped_column(Text)
    heard_about_us: orm.Mapped[Optional[str]] = orm.mapped_column(Text)
    job_function: orm.Mapped[Optional[str]] = orm.mapped_column(Text)
    job_title: orm.Mapped[Optional[str]] = orm.mapped_column(Text)
    onboarding_step: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=0, server_default=sa.text("0"))

    def __repr__(self):
        return f'<User {self.name}>'
    
    def to_dict(self):
        return {
            "uid": self.uid,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "company": self.company,
            "job_function": self.job_function,
            "job_title": self.job_title,
            "heard_about_us": self.heard_about_us,
            "onboarding_step": self.onboarding_step
        }
