def build_attack_chain(family):

    chains = {

        "Downloader": [

            "User Opens File",

            "PowerShell Executes",

            "Payload Downloaded",

            "Malware Installed"

        ],

        "PDF Auto Execution": [

            "User Opens PDF",

            "OpenAction Triggered",

            "Code Executed"

        ]
    }

    return chains.get(
        family,
        ["Unknown"]
    )