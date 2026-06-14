from backend.services.docscan.intelligence.remediation_engine import (
    remediation_advice
)

def build_summary(
    family,
    risk,
    systems,
    impact
):

    return f"""

Threat Family:
{family}

Risk:
{risk}

Affected Systems:
{systems}

Impact:
{impact}

Recommended Action:
{remediation_advice(family)}

"""