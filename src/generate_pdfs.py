"""
Generate synthetic healthcare claim PDFs for the Document Intelligence Pipeline.
Creates 500 realistic-looking claim forms with fake patient data and real medical codes.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from faker import Faker
import random
import os
from datetime import datetime, timedelta

# Set up Faker - this is our fake data generator
fake = Faker('en_US')
Faker.seed(42)  # Same seed = same fake data every run = reproducible
random.seed(42)

# Real ICD-10 diagnosis codes - common ones used in healthcare
ICD10_CODES = [
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("I10", "Essential (primary) hypertension"),
    ("J45.909", "Unspecified asthma, uncomplicated"),
    ("M54.5", "Low back pain"),
    ("K21.9", "Gastro-esophageal reflux disease without esophagitis"),
    ("F41.1", "Generalized anxiety disorder"),
    ("R51", "Headache"),
    ("J06.9", "Acute upper respiratory infection, unspecified"),
    ("M25.561", "Pain in right knee"),
    ("N39.0", "Urinary tract infection, site not specified"),
    ("R10.9", "Unspecified abdominal pain"),
    ("Z00.00", "Encounter for general adult medical examination"),
    ("H66.90", "Otitis media, unspecified"),
    ("L70.0", "Acne vulgaris"),
    ("R05", "Cough"),
]

# Real CPT procedure codes - common office visit and procedure codes
CPT_CODES = [
    ("99213", "Office visit, established patient, 20-29 minutes"),
    ("99214", "Office visit, established patient, 30-39 minutes"),
    ("99203", "Office visit, new patient, 30-44 minutes"),
    ("99204", "Office visit, new patient, 45-59 minutes"),
    ("85025", "Complete blood count with differential"),
    ("80053", "Comprehensive metabolic panel"),
    ("93000", "Electrocardiogram, complete"),
    ("71046", "Chest X-ray, 2 views"),
    ("90471", "Immunization administration"),
    ("96372", "Therapeutic injection"),
]

# Common US insurance companies
INSURANCE_COMPANIES = [
    "Blue Cross Blue Shield",
    "UnitedHealthcare",
    "Aetna",
    "Cigna",
    "Humana",
    "Kaiser Permanente",
    "Anthem",
    "Centene",
]
def generate_claim_pdf(claim_number, output_dir):
    """
    Generate a single healthcare claim PDF.
    
    Args:
        claim_number: Integer to make each claim unique (1, 2, 3, ...)
        output_dir: Folder where the PDF will be saved
    """
    
    # Generate unique claim ID
    claim_id = f"CLM-2026-{claim_number:05d}"  # Pads with zeros: CLM-2026-00001
    
    # Generate fake patient details
    patient_name = fake.name()
    patient_id = f"PT-{random.randint(100000, 999999)}"
    patient_dob = fake.date_of_birth(minimum_age=18, maximum_age=85)
    patient_address = fake.address().replace('\n', ', ')
    
    # Generate fake provider details
    provider_name = f"Dr. {fake.name()}"
    provider_npi = f"{random.randint(1000000000, 9999999999)}"  # NPI = 10 digits
    
    # Generate service details
    service_date = fake.date_between(start_date='-90d', end_date='today')
    
    # Pick random medical codes
    icd_code, icd_description = random.choice(ICD10_CODES)
    cpt_code, cpt_description = random.choice(CPT_CODES)
    
    # Generate claim amount based on procedure (realistic ranges)
    if cpt_code.startswith("99"):  # Office visits
        amount = round(random.uniform(150, 450), 2)
    elif cpt_code in ["85025", "80053"]:  # Lab work
        amount = round(random.uniform(50, 200), 2)
    elif cpt_code == "71046":  # Imaging
        amount = round(random.uniform(200, 600), 2)
    else:
        amount = round(random.uniform(75, 350), 2)
    
    # Pick insurance company
    insurance = random.choice(INSURANCE_COMPANIES)
    
    # File path
    pdf_path = os.path.join(output_dir, f"{claim_id}.pdf")
    
    # Build the PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("<b>HEALTHCARE CLAIM FORM</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Claim header
    claim_header = Paragraph(
        f"<b>Claim ID:</b> {claim_id}<br/>"
        f"<b>Date Submitted:</b> {datetime.now().strftime('%Y-%m-%d')}<br/>"
        f"<b>Insurance Carrier:</b> {insurance}",
        styles['Normal']
    )
    story.append(claim_header)
    story.append(Spacer(1, 0.3*inch))
    
    # Patient information section
    story.append(Paragraph("<b>PATIENT INFORMATION</b>", styles['Heading2']))
    patient_info = [
        ["Patient Name:", patient_name],
        ["Patient ID:", patient_id],
        ["Date of Birth:", patient_dob.strftime('%Y-%m-%d')],
        ["Address:", patient_address],
    ]
    patient_table = Table(patient_info, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Provider information section
    story.append(Paragraph("<b>PROVIDER INFORMATION</b>", styles['Heading2']))
    provider_info = [
        ["Provider Name:", provider_name],
        ["NPI Number:", provider_npi],
        ["Date of Service:", service_date.strftime('%Y-%m-%d')],
    ]
    provider_table = Table(provider_info, colWidths=[2*inch, 4*inch])
    provider_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(provider_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Claim details section
    story.append(Paragraph("<b>CLAIM DETAILS</b>", styles['Heading2']))
    claim_details = [
        ["Diagnosis Code (ICD-10):", icd_code],
        ["Diagnosis Description:", icd_description],
        ["Procedure Code (CPT):", cpt_code],
        ["Procedure Description:", cpt_description],
        ["Claim Amount:", f"${amount:,.2f}"],
    ]
    claim_table = Table(claim_details, colWidths=[2.5*inch, 3.5*inch])
    claim_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Highlight amount row
    ]))
    story.append(claim_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Footer
    footer = Paragraph(
        "<i>This is a synthetic claim generated for testing purposes only. "
        "No real patient data is contained in this document.</i>",
        styles['Italic']
    )
    story.append(footer)
    
    # Build the PDF file
    doc.build(story)
    
    return claim_id

def main():
    """Generate all 500 synthetic claim PDFs."""
    
    NUM_PDFS = 500
    OUTPUT_DIR = "data/raw_pdfs"
    
    # Make sure output folder exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Generating {NUM_PDFS} synthetic healthcare claim PDFs...")
    print(f"Output folder: {OUTPUT_DIR}")
    print("-" * 60)
    
    for i in range(1, NUM_PDFS + 1):
        claim_id = generate_claim_pdf(i, OUTPUT_DIR)
        
        # Print progress every 50 PDFs
        if i % 50 == 0:
            print(f"Progress: {i}/{NUM_PDFS} PDFs generated")
    
    print("-" * 60)
    print(f"Done! {NUM_PDFS} PDFs created in {OUTPUT_DIR}")
    print(f"Sample files:")
    print(f"  - {OUTPUT_DIR}/CLM-2026-00001.pdf")
    print(f"  - {OUTPUT_DIR}/CLM-2026-00250.pdf")
    print(f"  - {OUTPUT_DIR}/CLM-2026-00500.pdf")


if __name__ == "__main__":
    main()