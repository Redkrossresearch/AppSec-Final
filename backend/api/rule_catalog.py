from flask import Blueprint, current_app, jsonify
from flask_login import login_required

from backend.services.scanner.rule_engine import RuleEngine

rule_catalog_bp = Blueprint("rule_catalog", __name__, url_prefix="/api/rule-catalog")


@rule_catalog_bp.get("")
@login_required
def list_rules():
    engine = RuleEngine(current_app.config["RULES_DIR"])
    rules = [
        {
            "id": rule["id"],
            "title": rule["title"],
            "category": rule["category"],
            "severity": rule["severity"],
            "cvss_score": rule.get("cvss_score"),
            "fixable": rule.get("fixable", False),
        }
        for rule in engine.rules
    ]
    return jsonify({"rules": rules, "total": len(rules)})