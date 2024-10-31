import fitz  # PyMuPDF
import pdfplumber
import re

def clean_text(text):
    cleaned_text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip() 
    return cleaned_text

# def extract_marking_guide_data(pdf_file):
#     doc = fitz.open(pdf_file)
#     text = ""
#     for page in doc:
#         text += page.get_text()
#     return text

# def extract_criteria_and_marks(text):
#     # Example patterns for finding criteria and marks in the text
#     criteria_pattern = r"(Criterion \d+: .*?)(?:\n|$)"  # Extract criteria
#     marks_pattern = r"(Mark: \d+)"  # Extract marks (adjust regex based on actual format)

#     # Find all matching criteria and marks
#     criteria = re.findall(criteria_pattern, text)
#     marks = re.findall(marks_pattern, text)

#     # Returning criteria and marks
#     return criteria, marks

def format_table_for_ai(table):
    formatted_table = ""
    for row in table:
        formatted_row = ' | '.join(str(cell) if cell else '' for cell in row)  #handles None cells
        formatted_table += formatted_row + '\n'
    return formatted_table

def extract_text_and_tables_from_pdf(file_obj):
    text_by_page = []
    tables_by_page = {}

    try:
        #open file content using fitz (PyMuPDF) directly from file object stream
        doc = fitz.open(stream=file_obj.read(), filetype="pdf")

        if doc.is_encrypted:
            print("Skipping encrypted PDF")
            return "Error: PDF is encrypted."

        #extracting text page by page
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text("text-with-spaces")
            cleaned_page_text = clean_text(page_text)
            text_by_page.append(f"Page {page_num}:\n{cleaned_page_text}\n\n")

        file_obj.seek(0)  #resets file pointer for pdfplumber

    except Exception as e:
        print(f"First Extraction Method (PyMuPDF) failed: {e}")

    # Fallback: Try using pdfplumber for both text and tables
    try:
        with pdfplumber.open(file_obj) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                #extracts text from pdfplumber
                page_text = page.extract_text()
                if page_text:
                    cleaned_page_text = clean_text(page_text)
                    text_by_page.append(f"Page {i}:\n{cleaned_page_text}\n\n")

                #extracts tables from the page using pdfplumber
                page_tables = page.extract_tables()
                if page_tables:
                    formatted_tables = ""
                    for table in page_tables:
                        formatted_tables += format_table_for_ai(table) + "\n"
                    tables_by_page[i] = formatted_tables  #store formatted tables by page number

        return text_by_page, tables_by_page

    except Exception as e:
        print(f"Second Extraction Method (pdfplumber) failed: {e}")

    return "Error: Failed all text extraction", {}