from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify
from flask_login import current_user, login_required

from backend.extensions import db
from backend.models import AuditLog, Finding, Fix, Project, Scan
from backend.services.fixer.ai_fixer import build_ai_fix_preview
from backend.services.fixer.backup_manager import create_backup
from backend.services.fixer.patch_applier import apply_generated_patch
from backend.services.fixer.rollback import restore_backup

fixes_bp = Blueprint("fixes", __name__, url_prefix="/api")


def owned_finding(finding_id):
    return (
        Finding.query.join(Scan).join(Project)
        .filter(Finding.id == finding_id, Project.owner_id == current_user.id)
        .first_or_404()
    )


def owned_fix(fix_id):
    return (
        Fix.query.join(Finding).join(Scan).join(Project)
        .filter(Fix.id == fix_id, Project.owner_id == current_user.id)
        .first_or_404()
    )


@fixes_bp.post("/findings/<int:finding_id>/fix-preview")
@login_required
def preview_fix(finding_id):
    finding = owned_finding(finding_id)
    preview = build_ai_fix_preview(finding, finding.scan.project.path)
    if not preview["applicable"]:
        return jsonify({"error": preview.get("explanation", "Could not generate a fix."), **preview}), 422
    fix = Fix(
        finding_id=finding.id,
        explanation=preview["explanation"],
        original_content=preview["original_content"],
        fixed_content=preview["fixed_content"],
        diff=preview["diff"],
    )
    db.session.add(fix)
    db.session.commit()
    return jsonify({"applicable": True, "fix": fix.to_dict()}), 201


@fixes_bp.get("/fixes/<int:fix_id>")
@login_required
def get_fix(fix_id):
    return jsonify({"fix": owned_fix(fix_id).to_dict()})


@fixes_bp.post("/fixes/<int:fix_id>/apply")
@login_required
def apply_fix(fix_id):
    fix = owned_fix(fix_id)
    if fix.status != "proposed":
        return jsonify({"error": "Only proposed fixes can be applied."}), 409
    finding = fix.finding
    project = finding.scan.project
    backup = create_backup(project.path, finding.file_path,
                           current_app.config["SCAN_STORAGE"], project.id, fix.id)
    apply_generated_patch(project.path, finding.file_path, fix.original_content, fix.fixed_content)
    fix.backup_path = str(backup)
    fix.status = "applied"
    fix.applied_at = datetime.now(timezone.utc)
    finding.status = "fixed"
    db.session.add(AuditLog(user_id=current_user.id, action="apply_fix", entity_type="fix", entity_id=fix.id))
    db.session.commit()
    return jsonify({"fix": fix.to_dict(), "finding": finding.to_dict()})


@fixes_bp.post("/fixes/<int:fix_id>/rollback")
@login_required
def rollback_fix(fix_id):
    fix = owned_fix(fix_id)
    if fix.status != "applied":
        return jsonify({"error": "Only applied fixes can be rolled back."}), 409
    finding = fix.finding
    restore_backup(finding.scan.project.path, finding.file_path, fix.backup_path)
    fix.status = "rolled_back"
    fix.rolled_back_at = datetime.now(timezone.utc)
    finding.status = "open"
    db.session.add(AuditLog(user_id=current_user.id, action="rollback_fix", entity_type="fix", entity_id=fix.id))
    db.session.commit()
    return jsonify({"fix": fix.to_dict(), "finding": finding.to_dict()})


@fixes_bp.post("/scans/<int:scan_id>/fix-all")
@login_required
def fix_all(scan_id):
    """Apply all auto-fixable findings in a scan at once."""
    scan = (
        Scan.query.join(Project)
        .filter(Scan.id == scan_id, Project.owner_id == current_user.id)
        .first_or_404()
    )
    project = scan.project
    applied = []
    skipped = []
    errors = []

    fixable_findings = [f for f in scan.findings if f.fixable and f.status == "open"]

    for finding in fixable_findings:
        try:
            preview = build_ai_fix_preview(finding, project.path)
            if not preview["applicable"]:
                skipped.append({"id": finding.id, "title": finding.title, "reason": preview["explanation"]})
                continue

            fix = Fix(
                finding_id=finding.id,
                explanation=preview["explanation"],
                original_content=preview["original_content"],
                fixed_content=preview["fixed_content"],
                diff=preview["diff"],
            )
            db.session.add(fix)
            db.session.flush()

            backup = create_backup(project.path, finding.file_path,
                                   current_app.config["SCAN_STORAGE"], project.id, fix.id)
            apply_generated_patch(project.path, finding.file_path,
                                  fix.original_content, fix.fixed_content)
            fix.backup_path = str(backup)
            fix.status = "applied"
            fix.applied_at = datetime.now(timezone.utc)
            finding.status = "fixed"
            applied.append({"id": finding.id, "title": finding.title, "fix_id": fix.id})
        except Exception as e:
            errors.append({"id": finding.id, "title": finding.title, "error": str(e)})

    db.session.add(AuditLog(user_id=current_user.id, action="fix_all", entity_type="scan", entity_id=scan_id))
    db.session.commit()

    return jsonify({
        "applied": applied,
        "skipped": skipped,
        "errors": errors,
        "summary": f"Fixed {len(applied)} of {len(fixable_findings)} fixable issues."
    })
