import re

def scan_iocs(content):

    findings = []

    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

    ips = re.findall(
        ip_pattern,
        content
    )

    for ip in ips:

        findings.append({
            "type": "IP Address",
            "value": ip
        })

    return findings