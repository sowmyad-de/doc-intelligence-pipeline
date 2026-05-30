"""
Extract text from healthcare claim PDFs using pdfplumber.
This is Step 1 of our pipeline - turning unreadable PDF files into readable text
that we can later send to Claude for structured extraction.
"""

import pdfplumber
import os


def extract_text_from_pdf(pdf_path):
    """
    Open a PDF file and extract all the text inside it.
    
    Args:
        pdf_path: Full path to the PDF file (like "data/raw_pdfs/CLM-2026-00001.pdf")
    
    Returns:
        A string containing all the text from the PDF
    """
    
    # Open the PDF file
    # 'with' statement automatically closes the file when we're done - good practice
    with pdfplumber.open(pdf_path) as pdf:
        
        # A PDF can have multiple pages - we'll collect text from all pages
        all_text = ""
        
        # Loop through each page
        for page_number, page in enumerate(pdf.pages, start=1):
            
            # Extract text from this page
            page_text = page.extract_text()
            
            # Add a header so we know which page the text came from
            all_text += f"\n--- PAGE {page_number} ---\n"
            all_text += page_text
            all_text += "\n"
    
    return all_text


def main():
    """Test our extraction on a single PDF."""
    
    # Path to one of our generated PDFs
    test_pdf = "data/raw_pdfs/CLM-2026-00001.pdf"
    
    # Check the file actually exists
    if not os.path.exists(test_pdf):
        print(f"ERROR: PDF not found at {test_pdf}")
        print("Did you run generate_pdfs.py first?")
        return
    
    print(f"Reading PDF: {test_pdf}")
    print("=" * 60)
    
    # Extract the text
    extracted_text = extract_text_from_pdf(test_pdf)
    
    # Print it so we can see what we got
    print(extracted_text)
    
    print("=" * 60)
    print(f"Total characters extracted: {len(extracted_text)}")


if __name__ == "__main__":
    main()