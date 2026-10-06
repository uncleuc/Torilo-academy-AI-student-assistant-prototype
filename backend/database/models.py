"""SQLAlchemy 2.x models for the initial Torilo Academy data schema."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
	Boolean,
	CheckConstraint,
	DateTime,
	ForeignKey,
	Index,
	Integer,
	String,
	UniqueConstraint,
	func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
	"""Declarative base for all database models."""


class Instructor(Base):
	__tablename__ = "instructors"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	full_name: Mapped[str] = mapped_column(String(160), nullable=False)
	email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)

	courses: Mapped[list[Course]] = relationship(back_populates="instructor")


class Course(Base):
	__tablename__ = "courses"
	__table_args__ = (
		CheckConstraint("duration_weeks > 0", name="ck_courses_duration_positive"),
		Index("ix_courses_is_active_name", "is_active", "name"),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	name: Mapped[str] = mapped_column(String(180), nullable=False)
	description: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
	level: Mapped[str] = mapped_column(String(40), nullable=False, default="unspecified")
	duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	instructor_id: Mapped[int | None] = mapped_column(
		ForeignKey("instructors.id", ondelete="RESTRICT"), nullable=True, index=True
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)

	instructor: Mapped[Instructor | None] = relationship(back_populates="courses")
	classes: Mapped[list[Class]] = relationship(back_populates="course")
	enrollments: Mapped[list[Enrollment]] = relationship(back_populates="course")


class Class(Base):
	__tablename__ = "classes"
	__table_args__ = (
		CheckConstraint(
			"status IN ('planned', 'active', 'completed', 'cancelled')",
			name="ck_classes_status",
		),
		CheckConstraint("ends_at > starts_at", name="ck_classes_end_after_start"),
		Index("ix_classes_status_starts_at", "status", "starts_at"),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	course_id: Mapped[int] = mapped_column(
		ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
	)
	instructor_id: Mapped[int | None] = mapped_column(
		ForeignKey("instructors.id", ondelete="RESTRICT"), nullable=True, index=True
	)
	starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	location: Mapped[str | None] = mapped_column(String(240), nullable=True)
	status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")

	course: Mapped[Course] = relationship(back_populates="classes")
	instructor: Mapped[Instructor | None] = relationship()
	enrollments: Mapped[list[Enrollment]] = relationship(back_populates="class_instance")


class Student(Base):
	__tablename__ = "students"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	full_name: Mapped[str] = mapped_column(String(160), nullable=False)
	email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)

	enrollments: Mapped[list[Enrollment]] = relationship(back_populates="student")


class Enrollment(Base):
	__tablename__ = "enrollments"
	__table_args__ = (
		UniqueConstraint("student_id", "course_id", name="uq_enrollments_student_course"),
		CheckConstraint(
			"status IN ('enrolled', 'completed', 'withdrawn')",
			name="ck_enrollments_status",
		),
		Index("ix_enrollments_course_status", "course_id", "status"),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	student_id: Mapped[int] = mapped_column(
		ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
	)
	course_id: Mapped[int] = mapped_column(
		ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
	)
	class_id: Mapped[int | None] = mapped_column(
		ForeignKey("classes.id", ondelete="RESTRICT"), nullable=True, index=True
	)
	status: Mapped[str] = mapped_column(String(20), nullable=False, default="enrolled")
	enrolled_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)

	student: Mapped[Student] = relationship(back_populates="enrollments")
	course: Mapped[Course] = relationship(back_populates="enrollments")
	class_instance: Mapped[Class | None] = relationship(back_populates="enrollments")