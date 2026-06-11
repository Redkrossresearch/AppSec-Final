import json
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from backend.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="analyst")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    projects = db.relationship("Project", back_populates="owner", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "name": self.name, "role": self.role,
                "created_at": self.created_at.isoformat()}


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    path = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    owner = db.relationship("User", back_populates="projects")
    scans = db.relationship("Scan", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description,
                "path": self.path, "owner_id": self.owner_id,
                "created_at": self.created_at.isoformat(), "scan_count": len(self.scans)}


class Scan(db.Model):
    __tablename__ = "scans"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="queued")
    total_files = db.Column(db.Integer, nullable=False, default=0)
    summary_json = db.Column(db.Text, nullable=False, default="{}")
    error = db.Column(db.Text)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)
    project = db.relationship("Project", back_populates="scans")
    findings = db.relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    reports = db.relationship("Report", back_populates="scan", cascade="all, delete-orphan")

    @property
    def summary(self):
        return json.loads(self.summary_json or "{}")

    def set_summary(self, value):
        self.summary_json = json.dumps(value)

    def to_dict(self):
        return {"id": self.id, "project_id": self.project_id, "status": self.status,
                "total_files": self.total_files, "finding_count": len(self.findings),
                "summary": self.summary, "error": self.error,
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None}


class Finding(db.Model):
    __tablename__ = "findings"
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scans.id"), nullable=False, index=True)
    rule_id = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    line_number = db.Column(db.Integer)
    line_text = db.Column(db.Text, nullable=False, default="")
    recommendation = db.Column(db.Text, nullable=False, default="")
    cvss_score = db.Column(db.Float, nullable=False, default=0.0)
    fixable = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(30), nullable=False, default="open")
    scan = db.relationship("Scan", back_populates="findings")
    fixes = db.relationship("Fix", back_populates="finding", cascade="all, delete-orphan")

    def to_dict(self):
        latest_fix = self.fixes[-1].to_dict() if self.fixes else None
        return {"id": self.id, "scan_id": self.scan_id, "rule_id": self.rule_id,
                "category": self.category, "severity": self.severity, "title": self.title,
                "description": self.description, "file_path": self.file_path,
                "line_number": self.line_number, "line_text": self.line_text,
                "recommendation": self.recommendation, "cvss_score": self.cvss_score,
                "fixable": self.fixable, "status": self.status, "fix": latest_fix}


class Fix(db.Model):
    __tablename__ = "fixes"
    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="proposed")
    explanation = db.Column(db.Text, nullable=False, default="")
    original_content = db.Column(db.Text)
    fixed_content = db.Column(db.Text)
    diff = db.Column(db.Text, nullable=False, default="")
    backup_path = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    applied_at = db.Column(db.DateTime)
    rolled_back_at = db.Column(db.DateTime)
    finding = db.relationship("Finding", back_populates="fixes")

    def to_dict(self, include_contents=False):
        data = {"id": self.id, "finding_id": self.finding_id, "status": self.status,
                "explanation": self.explanation, "diff": self.diff,
                "created_at": self.created_at.isoformat(),
                "applied_at": self.applied_at.isoformat() if self.applied_at else None,
                "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None}
        if include_contents:
            data.update({"original_content": self.original_content, "fixed_content": self.fixed_content})
        return data


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scans.id"), nullable=False)
    format = db.Column(db.String(10), nullable=False)
    output_path = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    scan = db.relationship("Scan", back_populates="reports")

    def to_dict(self):
        return {"id": self.id, "scan_id": self.scan_id, "format": self.format,
                "output_path": self.output_path, "created_at": self.created_at.isoformat()}


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(60), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {"id": self.id, "action": self.action, "entity_type": self.entity_type,
                "entity_id": self.entity_id, "details": self.details,
                "created_at": self.created_at.isoformat()}
