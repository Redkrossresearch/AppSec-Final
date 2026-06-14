def extract_embedded_objects(content):

    findings = []

    indicators = [

        "/EmbeddedFile",
        "/Filespec",
        "/ObjStm",
        "/Launch",
        "/OpenAction",
        "/JavaScript"

    ]

    for indicator in indicators:

        if indicator.lower() in content.lower():

            findings.append(
                indicator
            )

    return findings