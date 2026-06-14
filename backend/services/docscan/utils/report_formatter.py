def format_report(findings):

    lines = []

    for item in findings:

        lines.append(

            f"{item['type']} : "
            f"{item['value']}"

        )

    return "\n".join(
        lines
    )