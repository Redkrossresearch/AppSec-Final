def extract_actions(content):

    actions = []

    keywords = [

        "/OpenAction",
        "/Launch",
        "/SubmitForm",
        "/ImportData",
        "/JavaScript"

    ]

    for keyword in keywords:

        if keyword.lower() in content.lower():

            actions.append(keyword)

    return actions