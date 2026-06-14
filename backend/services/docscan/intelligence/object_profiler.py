def profile_object(content):

    content = content.lower()

    if "/javascript" in content:

        return {

            "risk": "HIGH",

            "type": "JavaScript Object"

        }

    if "openaction" in content:

        return {

            "risk": "HIGH",

            "type": "Auto Execution"

        }

    if "/launch" in content:

        return {

            "risk": "CRITICAL",

            "type": "Launch Action"

        }

    return {

        "risk": "LOW",

        "type": "Unknown"

    }