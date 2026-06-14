import zipfile
import os

def scan_zip(file_path):

    findings = []

    try:

        with zipfile.ZipFile(file_path, "r") as z:

            files = z.namelist()

            findings.append({
                "type": "Files Inside ZIP",
                "value": len(files)
            })

            for file in files:

                findings.append({
                    "type": "Contained File",
                    "value": file
                })

                if file.endswith(".exe"):

                    findings.append({
                        "type": "High Risk",
                        "value": file
                    })

    except Exception as e:

        findings.append({
            "type": "Error",
            "value": str(e)
        })

    return findings