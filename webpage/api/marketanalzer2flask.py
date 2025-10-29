from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import tempfile
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
GEMINI_API_KEY = "AIzaSyDypFnhI414PHOFko39rSP33iWK4PugCBE"
client = genai.Client(api_key=GEMINI_API_KEY)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ========== FINANCIAL DATA EXTRACTION FUNCTIONS ==========

EXTRACTION_PROMPT = """
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
  "company": "",
  "net_worth": ,
  "liabilities": ,
  "equity": ,
  "profit_and_loss": {
    "total_revenue": ,
    "total_expenses": ,
    "net_profit_or_loss": 
  }
}
"""

def extract_financial_data_from_pdf(pdf_path):
    """Extract financial data from PDF using Gemini."""
    try:
        # Upload the file
        uploaded_file = client.files.upload(file=pdf_path)
        
        # Generate content
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part(text=EXTRACTION_PROMPT),
                types.Part(file_data=types.FileData(file_uri=uploaded_file.uri))
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
        )
        
        financial_data = json.loads(response.text.strip())
        
        # Delete uploaded file to clean up
        client.files.delete(name=uploaded_file.name)
        
        return financial_data
    except Exception as e:
        return {"error": str(e)}

def calculate_financial_ratios(company_data):
    """Calculate key financial ratios from company financial data."""
    try:
        # Extract values
        liabilities = company_data.get("liabilities", 0)
        equity = company_data.get("equity", 0)
        net_worth = company_data.get("net_worth", 0)
        
        # Calculate total assets
        assets = net_worth + liabilities if net_worth > 0 else equity + liabilities
        
        profit_loss = company_data.get("profit_and_loss", {})
        revenue = profit_loss.get("total_revenue", 0)
        expenses = profit_loss.get("total_expenses", 0)
        net_profit = profit_loss.get("net_profit_or_loss", 0)
        
        # Calculate ratios
        ratios = {
            "company": company_data.get("company", "Unknown"),
            # Profitability Ratios
            "net_profit_margin_percent": round((net_profit / revenue * 100) if revenue > 0 else 0, 2),
            "return_on_equity_percent": round((net_profit / equity * 100) if equity > 0 else 0, 2),
            "return_on_assets_percent": round((net_profit / assets * 100) if assets > 0 else 0, 2),
            # Liquidity Ratios
            "current_ratio": round((assets / liabilities) if liabilities > 0 else 0, 2),
            # Leverage Ratios
            "debt_to_equity_ratio": round((liabilities / equity) if equity > 0 else 0, 2),
            # Efficiency Ratios
            "asset_turnover_ratio": round((revenue / assets) if assets > 0 else 0, 2),
            # Raw financial data
            "total_assets": assets,
            "total_liabilities": liabilities,
            "total_equity": equity,
            "total_revenue": revenue,
            "net_profit": net_profit
        }
        
        return ratios
    except Exception as e:
        return {"error": str(e)}

def ai_market_analysis_with_grounding(company_ratios):
    """Use Gemini AI with Google Search grounding for market analysis."""
    company_name = company_ratios.get('company', 'Unknown')
    
    prompt = f"""
You are a financial analyst expert. Analyze the following company's financial ratios and provide a comprehensive market comparison using the latest available market data.

Company: {company_name}

Financial Ratios:
- Net Profit Margin: {company_ratios.get('net_profit_margin_percent')}%
- Return on Equity (ROE): {company_ratios.get('return_on_equity_percent')}%
- Return on Assets (ROA): {company_ratios.get('return_on_assets_percent')}%
- Current Ratio: {company_ratios.get('current_ratio')}
- Debt-to-Equity Ratio: {company_ratios.get('debt_to_equity_ratio')}
- Asset Turnover: {company_ratios.get('asset_turnover_ratio')}

Financial Data:
- Total Assets: ${company_ratios.get('total_assets'):,.0f}
- Total Revenue: ${company_ratios.get('total_revenue'):,.0f}
- Net Profit: ${company_ratios.get('net_profit'):,.0f}

Provide your analysis in the following JSON format:
{{
  "company": "{company_name}",
  "overall_health_score": <0-100 score>,
  "performance_grade": "",
  "industry_comparison": {{
    "profitability": "",
    "liquidity": "",
    "leverage": "",
    "efficiency": ""
  }},
  "key_strengths": ["", "", ""],
  "key_weaknesses": ["", "", ""],
  "market_position": "",
  "investment_outlook": "",
  "recommendations": ["", "", ""]
}}
"""
    
    try:
        # Try with Google Search grounding
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[types.Part(text=prompt)],
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            ),
            tools=[{"google_search": {}}]
        )
        
        analysis = json.loads(response.text.strip())
        analysis["grounding_enabled"] = True
        return analysis
    except Exception as e:
        # Fallback without grounding
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[types.Part(text=prompt)],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            
            analysis = json.loads(response.text.strip())
            analysis["grounding_enabled"] = False
            analysis["note"] = "Analysis based on model knowledge"
            return analysis
        except Exception as e2:
            return {"error": str(e2)}

# ========== FLASK API ENDPOINTS ==========

@app.route('/api/extract', methods=['POST'])
def extract_financial_data():
    """
    Endpoint for simple financial data extraction.
    Upload a PDF and get extracted financial data as JSON.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        # Extract financial data
        result = extract_financial_data_from_pdf(temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_complete():
    """
    Endpoint for complete financial analysis with AI market insights.
    Upload a PDF and get:
    1. Extracted financial data
    2. Calculated financial ratios
    3. AI-powered market analysis
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        # Step 1: Extract financial data
        financial_data = extract_financial_data_from_pdf(temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if "error" in financial_data:
            return jsonify({"error": financial_data["error"]}), 500
        
        # Step 2: Calculate ratios
        ratios = calculate_financial_ratios(financial_data)
        
        if "error" in ratios:
            return jsonify({"error": ratios["error"]}), 500
        
        # Step 3: AI market analysis
        ai_analysis = ai_market_analysis_with_grounding(ratios)
        
        # Combine all results
        complete_result = {
            "financial_data": financial_data,
            "financial_ratios": ratios,
            "market_analysis": ai_analysis
        }
        
        return jsonify(complete_result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok", "message": "API is running"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
