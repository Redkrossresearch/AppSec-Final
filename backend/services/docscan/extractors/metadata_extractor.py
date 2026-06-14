from PyPDF2 import PdfReader

def extract_pdf_metadata(file_path):

    try:
        reader = PdfReader(file_path)
        return reader.metadata
    except:
        return {}