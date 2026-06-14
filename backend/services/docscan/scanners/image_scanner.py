from PIL import Image
import os

def scan_image(file_path):

    findings = []

    try:

        img = Image.open(file_path)

        findings.append({
            "type": "Image Format",
            "value": img.format
        })

        findings.append({
            "type": "Dimensions",
            "value": f"{img.width} x {img.height}"
        })

        findings.append({
            "type": "Color Mode",
            "value": img.mode
        })

        findings.append({
            "type": "File Name",
            "value": os.path.basename(file_path)
        })

    except Exception as e:

        findings.append({
            "type": "Error",
            "value": str(e)
        })

    return findings