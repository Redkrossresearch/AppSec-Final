import re

def extract_pdf_objects(file_path):

    objects = []

    try:

        with open(
            file_path,
            "rb"
        ) as f:

            content = f.read().decode(
                errors="ignore"
            )

        matches = re.findall(

            r'(\d+\s+\d+\s+obj.*?endobj)',

            content,

            re.DOTALL

        )

        for i, obj in enumerate(matches):

            objects.append({

                "id": i + 1,

                "content": obj[:1000]

            })

    except Exception as e:

        objects.append({

            "id": "Error",

            "content": str(e)

        })

    return objects