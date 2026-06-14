def build_executive_summary(
    family,
    risk,
    findings_count
):

    return f"""

Threat Family: {family}

Risk Level: {risk}

Indicators Found: {findings_count}

This document contains
suspicious indicators that
require further investigation.

"""