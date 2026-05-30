"""Batch process all PDFs through Claude API."""
import os
import json
import time
import glob
from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from extract_pdf import extract_text_from_pdf

load_dotenv()
client = Anthropic()
CLAUDE_MODEL = "claude-haiku-4-5-20251001"


class ClaimData(BaseModel):
    claim_id: str = Field(description="Claim ID")
    patient_name: str = Field(description="Patient name")
    patient_id: str = Field(description="Patient ID")
    patient_dob: str = Field(description="Date of birth YYYY-MM-DD")
    provider_name: str = Field(description="Provider name")
    provider_npi: str = Field(description="NPI number")
    service_date: str = Field(description="Service date YYYY-MM-DD")
    diagnosis_code: str = Field(description="ICD-10 code")
    diagnosis_description: str = Field(description="Diagnosis description")
    procedure_code: str = Field(description="CPT code")
    procedure_description: str = Field(description="Procedure description")
    claim_amount: float = Field(description="Claim amount in dollars")
    insurance_carrier: str = Field(description="Insurance company")


def extract_claim_data(claim_text):
    schema = json.dumps(ClaimData.model_json_schema(), indent=2)
    prompt = f"""Extract healthcare claim data as JSON matching this schema:
{schema}

Rules: Return ONLY JSON. No markdown. No explanation. Dates as YYYY-MM-DD. Amount as number.

Claim text:
{claim_text}

JSON:"""
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    data = json.loads(text.strip())
    return ClaimData(**data).model_dump()


def process_single_pdf(pdf_path, output_dir):
    filename = os.path.basename(pdf_path).replace('.pdf', '')
    output_path = os.path.join(output_dir, f"{filename}.json")
    if os.path.exists(output_path):
        return {"filename": filename, "status": "skipped", "duration_seconds": 0}
    start = time.time()
    try:
        text = extract_text_from_pdf(pdf_path)
        data = extract_claim_data(text)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        return {"filename": filename, "status": "success", "duration_seconds": round(time.time() - start, 2)}
    except Exception as e:
        return {"filename": filename, "status": "failed", "error": str(e), "duration_seconds": round(time.time() - start, 2)}


def batch_process_all_pdfs():
    INPUT_DIR = "data/raw_pdfs"
    OUTPUT_DIR = "data/extracted_json"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_files = sorted(glob.glob(f"{INPUT_DIR}/*.pdf"))
    total = len(pdf_files)
    print(f"Found {total} PDFs to process")
    print("=" * 60)
    results = []
    success = failed = skipped = 0
    start = time.time()
    for i, pdf in enumerate(pdf_files, 1):
        r = process_single_pdf(pdf, OUTPUT_DIR)
        results.append(r)
        if r["status"] == "success":
            success += 1
        elif r["status"] == "failed":
            failed += 1
            print(f"  FAILED: {r['filename']} - {r.get('error', '')}")
        else:
            skipped += 1
        if i % 25 == 0 or i == total:
            elapsed = time.time() - start
            avg = elapsed / i
            eta = (total - i) * avg
            print(f"  {i}/{total} | OK:{success} Fail:{failed} Skip:{skipped} | {avg:.2f}s/PDF | ETA: {eta/60:.1f}min")
    duration = time.time() - start
    print("=" * 60)
    print(f"DONE | Total: {total} | OK: {success} | Failed: {failed} | Skipped: {skipped}")
    print(f"Time: {duration/60:.2f}min | Avg: {duration/total:.2f}s/PDF")
    os.makedirs("monitoring", exist_ok=True)
    with open("monitoring/extraction_metrics.json", 'w') as f:
        json.dump({"total": total, "success": success, "failed": failed, "skipped": skipped,
                   "duration_seconds": round(duration, 2), "results": results}, f, indent=2)
    print("Metrics saved to monitoring/extraction_metrics.json")


if __name__ == "__main__":
    batch_process_all_pdfs()
