def profile_code(code):

    report = []

    for item in code:

        item_lower = item.lower()

        if "eval(" in item_lower:

            report.append({

                "risk": "HIGH",

                "family": "Obfuscated Script",

                "impact":
                "May execute arbitrary code"

            })

        elif "openaction" in item_lower:

            report.append({

                "risk": "HIGH",

                "family": "PDF Auto Execution",

                "impact":
                "Triggers automatically on open"

            })

        elif "powershell" in item_lower:

            report.append({

                "risk": "CRITICAL",

                "family": "Downloader",

                "impact":
                "Downloads payloads from internet"

            })

    return report