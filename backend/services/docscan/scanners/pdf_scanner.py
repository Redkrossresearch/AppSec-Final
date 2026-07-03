from PyPDF2 import PdfReader
from backend.services.docscan.extractors.payload_extractor import (
    extract_payloads
)

from backend.services.docscan.extractors.shellcode_extractor import (
    extract_shellcode
)

from backend.services.docscan.extractors.command_extractor import (
    extract_commands
)

from backend.services.docscan.scanners.powershell_scanner import (
    detect_powershell
)

from backend.services.docscan.scanners.shellcode_scanner import (
    detect_shellcode
)

from backend.services.docscan.scanners.exploit_scanner import (
    detect_exploits
)

from backend.services.docscan.scanners.suspicious_api_scanner import (
    detect_suspicious_apis
)

from backend.services.docscan.scanners.malware_signature_scanner import (
    scan_signatures
)

from backend.services.docscan.intelligence.behavior_analyzer import (
    analyze_behavior
)

from backend.services.docscan.intelligence.persistence_detector import (
    detect_persistence
)

from backend.services.docscan.intelligence.reputation_engine import (
    reputation
)

from backend.services.docscan.intelligence.confidence_engine import (
    confidence_score
)

from backend.services.docscan.intelligence.exploitability_engine import (
    exploitability_score
)

from backend.services.docscan.intelligence.attack_chain_builder import (
    build_attack_chain
)

from backend.services.docscan.intelligence.mitre_mapper import (
    mitre_lookup
)
from backend.services.docscan.utils.hash_utils import calculate_sha256
from backend.services.docscan.intelligence.recommendation_engine import (
    generate_recommendations
)
from backend.services.docscan.extractors.embedded_content_extractor import (
    extract_embedded_files
)
from backend.services.docscan.extractors.raw_code_extractor import (
    extract_raw_code
)

from backend.services.docscan.intelligence.executive_summary import (
    build_executive_summary
)

from backend.services.docscan.sanitizers.pdf_sanitizer import (
    sanitize_pdf
)
from backend.services.docscan.scanners.javascript_scanner import detect_javascript
from backend.services.docscan.scanners.ioc_scanner import scan_iocs
from backend.services.docscan.scanners.yara_scanner import yara_scan

from backend.services.docscan.extractors.embedded_file_extractor import (
    extract_embedded_objects
)

from backend.services.docscan.intelligence.family_detector import (
    detect_family
)

from backend.services.docscan.intelligence.risk_engine import (
    calculate_risk
)

import os
import re


def scan_pdf(file_path, sanitized_dir=None):

    findings = []

    try:

        reader = PdfReader(file_path)

        findings.append({
            "type": "File Name",
            "value": os.path.basename(file_path)
        })

        findings.append({
            "type": "Pages",
            "value": len(reader.pages)
        })

        findings.append({
            "type": "SHA256",
            "value": calculate_sha256(file_path)
        })

        findings.append({
            "type": "Metadata",
            "value": str(reader.metadata)
        })

        text = ""

        for page in reader.pages:

            try:
                text += page.extract_text() or ""
            except:
                pass

        urls = re.findall(
            r'https?://[^\s]+',
            text
        )

        findings.append({
            "type": "URLs Found",
            "value": len(urls)
        })

        for url in urls:

            findings.append({
                "type": "URL",
                "value": url
            })

        # --- FIX #1: Read content first, then extract everything outside the 'with' block ---
        with open(file_path, "rb") as f:
            raw_content = f.read()
        content = raw_content.decode(
            "latin-1",
            errors="ignore"
)

        # Now all extractions happen after the file is closed
        payloads = extract_payloads(content)
        for item in payloads:
            findings.append({
                "type": "Payload",
                "value": item
            })

        commands = extract_commands(content)
        for item in commands:
            findings.append({
                "type": "Command",
                "value": item
            })

        shellcodes = extract_shellcode(content)
        for item in shellcodes:
            findings.append({
                "type": "Shellcode",
                "value": item
            })

        embedded_files = extract_embedded_files(content)
        for item in embedded_files:
            findings.append({
                "type": "Embedded File",
                "value": item
            })

        # Hidden Code Extraction
        hidden_code = extract_raw_code(content)
        for item in hidden_code:
            findings.append({
                "type": "Hidden Code",
                "value": item
            })

        # JavaScript Indicators
        js_findings = detect_javascript(content)
        for item in js_findings:
            findings.append({
                "type": "Suspicious",
                "value": item
            })

        powershell = detect_powershell(content)
        for item in powershell:
            findings.append({
                "type": "PowerShell Indicator",
                "value": item
            })

        shellcode_hits = detect_shellcode(content)
        for item in shellcode_hits:
            findings.append({
                "type": "Shellcode Indicator",
                "value": item
            })

        exploits = detect_exploits(content)
        for item in exploits:
            findings.append({
                "type": "Exploit Indicator",
                "value": item
            })

        apis = detect_suspicious_apis(content)
        for item in apis:
            findings.append({
                "type": "Suspicious API",
                "value": item
            })

        signatures = scan_signatures(content)
        for item in signatures:
            findings.append({
                "type": "Malware Signature",
                "value": item
            })

        # Embedded Objects
        embedded = extract_embedded_objects(content)
        for item in embedded:
            findings.append({
                "type": "Embedded Object",
                "value": item
            })

        # IOC Scan
        ioc_results = scan_iocs(content)
        for item in ioc_results:
            findings.append({
                "type": item["type"],
                "value": item["value"]
            })

        # YARA Scan
        yara_results = yara_scan(content)
        for item in yara_results:
            findings.append({
                "type": "YARA Match",
                "value": item["rule"]
            })

        # Threat Family
        family = detect_family(content)
        findings.append({
            "type": "Threat Family",
            "value": family
        })

        mitre = mitre_lookup(family)
        findings.append({
            "type": "MITRE Technique",
            "value": mitre
        })

        attack_chain = build_attack_chain(family)
        findings.append({
            "type": "Attack Chain",
            "value": " -> ".join(attack_chain)
        })

        rep = reputation(family)
        findings.append({
            "type": "Reputation",
            "value": rep
        })

        behavior = analyze_behavior(content)
        for item in behavior:
            findings.append({
                "type": "Behavior",
                "value": item
            })

        persistence = detect_persistence(content)
        for item in persistence:
            findings.append({
                "type": "Persistence",
                "value": item
            })

        # --- FIX #2: Improved Risk Calculation ---
        code_count = (
            len(js_findings)
            + len(payloads)
            + len(commands)
            + len(shellcode_hits)
            + len(apis)
            + len(exploits)
        )
        action_count = len(yara_results)
        embedded_count = len(embedded)

        risk = calculate_risk(
            code_count,
            action_count,
            embedded_count
        )

        findings.append({
            "type": "Risk Score",
            "value": risk
        })

        confidence = confidence_score(findings)
        findings.append({
            "type": "Confidence",
            "value": confidence
        })

        exploitability = exploitability_score(risk)
        findings.append({
            "type": "Exploitability",
            "value": exploitability
        })

        # Recommendations
        recommendations = generate_recommendations(
            family,
            risk
        )
        for item in recommendations:
            findings.append({
                "type": "Recommendation",
                "value": item
            })

        # --- NEW: Statistics Section ---
        findings.append({
            "type": "Statistics",
            "value": f"""
Payloads: {len(payloads)}
Commands: {len(commands)}
Shellcodes: {len(shellcodes)}
Embedded Files: {len(embedded_files)}
JavaScript: {len(js_findings)}
YARA Matches: {len(yara_results)}
"""
        })

        # Optional: Total Findings before Executive Summary
        findings.append({
            "type": "Total Findings",
            "value": len(findings)
        })

        # Executive Summary
        summary = build_executive_summary(
            family,
            risk,
            len(findings)
        )
        findings.append({
            "type": "Executive Summary",
            "value": summary
        })

        # Sanitized File — sanitize_pdf now returns {"output_file", "removed"}; the
        # emitted finding keeps its {type, value=path} shape so the adapter mapping is
        # unchanged. The removal report rides along for provable-sanitization checks.
        sanitize_result = sanitize_pdf(file_path, output_folder=sanitized_dir)
        safe_file = sanitize_result.get("output_file")
        findings.append({
            "type": "Sanitized File",
            "value": safe_file
        })

    except Exception as e:
        findings.append({
            "type": "Error",
            "value": str(e)
        })
    return findings