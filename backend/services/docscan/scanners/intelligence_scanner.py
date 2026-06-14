from backend.services.docscan.intelligence.threat_lookup import lookup_indicator

def build_threat_report(indicators):

    report = []

    for item in indicators:

        info = lookup_indicator(item)

        report.append({

            "indicator": item,

            "family": info["family"],

            "risk": info["risk"],

            "systems": info["systems"],

            "impact": info["impact"]
        })

    return report