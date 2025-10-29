from google import genai
from google.genai import types
import json
import os
import glob


# --- CONFIG ---
API_KEY = "AIzaSyDypFnhI414PHOFko39rSP33iWK4PugCBE"
client = genai.Client(api_key=API_KEY)


# PDF files to process (can be a list of paths or a folder pattern)
pdf_files = glob.glob("PDF_files/*.pdf")  # Automatically finds all PDFs in current directory


# --- Prompt Template ---
PROMPT_TEMPLATE = """
You are a financial data extraction assistant.
Read the uploaded company financial report (PDF) and extract the following values in pure numeric form.

First, identify the company name from the document itself (usually found in the header, title, or footer).

Always return numbers only (no currency symbols, commas, text, or words like 'million' or 'approximately').
If a number cannot be found, write 0.

Extract:
1. Company Name (extract from the document)
2. Net Worth (total assets minus total liabilities)
3. Total Liabilities (what the company owes)
4. Total Equity (owner/shareholders' ownership value)
5. Statement of Profit or Loss:
   a. Total Revenue
   b. Total Expenses
   c. Net Profit or Loss

Important formatting rules:
- Company name must be extracted from the PDF document itself
- All numeric values must be numbers only
- Do not include symbols, commas, text, or units in numeric fields
- If the number is unavailable, use 0
- Return only JSON, no explanation

Output format:
{
  "company": "<extracted company name from document>",
  "net_worth": <number>,
  "liabilities": <number>,
  "equity": <number>,
  "profit_and_loss": {
    "total_revenue": <number>,
    "total_expenses": <number>,
    "net_profit_or_loss": <number>
  }
}
"""


def analyze_financials(pdf_path):
    """Uploads a company PDF and extracts numeric financial data with auto-detected company name."""
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = pdf_file.read()

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part(text=PROMPT_TEMPLATE),
                types.Part.from_bytes(data=pdf_data, mime_type="application/pdf")
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
        )

        text_output = response.text.strip()

        try:
            result = json.loads(text_output)
            result["source_file"] = pdf_path
            return result
        except json.JSONDecodeError:
            print(f"⚠️ Gemini output not valid JSON for {pdf_path}, saving raw text.")
            return {"source_file": pdf_path, "raw_output": text_output}

    except Exception as e:
        print(f"❌ Error analyzing {pdf_path}: {e}")
        return {"source_file": pdf_path, "error": str(e)}


if __name__ == "__main__":
    results = []

    if not pdf_files:
        print("⚠️ No PDF files found in the current directory.")
    else:
        for pdf_path in pdf_files:
            print(f"🔍 Processing {pdf_path} ...")
            result = analyze_financials(pdf_path)
            results.append(result)

    # Save all results to one JSON file
    with open("financial_summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("✅ Extraction complete! Results saved to financial_summary.json")