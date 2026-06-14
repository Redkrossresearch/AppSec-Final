ALLOWED_EXTENSIONS = {

    "pdf",
    "docx",
    "zip",
    "xlsx",
    "pptx",
    "png",
    "jpg",
    "jpeg"

}

def allowed_file(filename):

    return (
        "." in filename and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )