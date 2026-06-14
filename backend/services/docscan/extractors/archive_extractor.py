import zipfile

def extract_archive_info(file_path):

    findings = []

    try:

        with zipfile.ZipFile(
            file_path,
            "r"
        ) as z:

            files = z.namelist()

            for file in files:

                findings.append({
                    "name": file
                })

    except Exception as e:

        findings.append({
            "error": str(e)
        })

    return findings