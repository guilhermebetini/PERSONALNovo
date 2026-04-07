from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

pdf_path = r'c:\Users\2024108060024\Downloads\OpiniAki - Avaliação - Luh.pdf'
extracted_text = extract_text_from_pdf(pdf_path)
print(extracted_text)