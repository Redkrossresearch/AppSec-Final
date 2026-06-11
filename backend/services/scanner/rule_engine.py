import json
import re
from pathlib import Path


class RuleEngine:
    def __init__(self, rules_dir):
        self.rules_dir = Path(rules_dir)
        self.rules = self._load_detection_rules()

    def _load_detection_rules(self):
        rules = []
        for path in sorted(self.rules_dir.rglob("*.json")):
            if path.name == "vulnerable_packages.json":
                continue
            with path.open(encoding="utf-8") as stream:
                rule = json.load(stream)
            rule["_compiled"] = re.compile(rule["pattern"])
            rules.append(rule)
        return rules

    def matching_rules(self, suffix):
        return [rule for rule in self.rules if suffix in rule.get("extensions", [])]
