def build_analysis_text(

    family,

    risk,

    systems,

    impact,

    recommendations

):

    text = f"""

Threat Family:
{family}

Risk:
{risk}

Affected Systems:
{systems}

Impact:
{impact}

Recommendations:

"""

    for item in recommendations:

        text += f"\n- {item}"

    return text