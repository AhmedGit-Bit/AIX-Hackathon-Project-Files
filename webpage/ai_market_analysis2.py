import json
import glob
from google import genai
from google.genai import types


# --- CONFIG ---
GEMINI_API_KEY = "AIzaSyDypFnhI414PHOFko39rSP33iWK4PugCBE"
client = genai.Client(api_key=GEMINI_API_KEY)


def extract_financial_data_from_pdf(pdf_path):
    """
    Extract financial data directly from PDF using Gemini.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with extracted financial data
    """
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
    
    try:
        # Upload the file - CORRECT syntax for SDK v1.46.0
        uploaded_file = client.files.upload(file=pdf_path)
        
        # Use the uploaded file in the request
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
        financial_data["source_file"] = pdf_path
        
        # Delete the uploaded file to clean up
        client.files.delete(name=uploaded_file.name)
        
        return financial_data

    except Exception as e:
        print(f"❌ Error extracting data from {pdf_path}: {e}")
        return {"source_file": pdf_path, "error": str(e)}


def calculate_financial_ratios(company_data):
    """
    Calculate key financial ratios from company financial data.
    
    Args:
        company_data: Dictionary containing company financial information
        
    Returns:
        Dictionary with calculated financial ratios
    """
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
        
        # Calculate ratios (with zero-division protection)
        ratios = {
            "company": company_data.get("company", "Unknown"),
            "source_file": company_data.get("source_file", ""),
            
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
            
            # Raw financial data for reference
            "total_assets": assets,
            "total_liabilities": liabilities,
            "total_equity": equity,
            "total_revenue": revenue,
            "net_profit": net_profit
        }
        
        return ratios
        
    except Exception as e:
        return {
            "company": company_data.get("company", "Unknown"),
            "error": str(e)
        }


def ai_market_analysis_with_grounding(company_ratios):
    """
    Use Gemini AI with Google Search grounding to analyze company performance 
    against real-time market standards.
    
    Args:
        company_ratios: Dictionary with calculated financial ratios
        
    Returns:
        AI-generated market analysis with performance scoring based on live data
    """
    
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

IMPORTANT: Search online for current industry benchmarks and competitor data for {company_name}'s sector. 
Look for:
1. Current industry average profit margins for this company's sector
2. Typical ROE and ROA ranges for similar companies
3. Standard liquidity and leverage ratios in this industry
4. Recent market trends and sector performance (2024-2025)
5. Competitor financial metrics if available

Provide your analysis in the following JSON format:
{{
  "company": "{company_name}",
  "overall_health_score": <0-100 score>,
  "performance_grade": "<A+, A, B+, B, C+, C, D, F>",
  "industry_comparison": {{
    "profitability": "<Above Market/At Market/Below Market>",
    "liquidity": "<Strong/Adequate/Weak>",
    "leverage": "<Conservative/Moderate/Aggressive>",
    "efficiency": "<High/Moderate/Low>"
  }},
  "key_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "key_weaknesses": ["<weakness 1>", "<weakness 2>", "<weakness 3>"],
  "market_position": "<Brief summary of market position based on searched data>",
  "investment_outlook": "<Positive/Neutral/Negative>",
  "recommendations": ["<recommendation 1>", "<recommendation 2>", "<recommendation 3>"],
  "detailed_analysis": {{
    "profitability_analysis": "<Analysis paragraph with specific industry comparisons from search>",
    "liquidity_analysis": "<Analysis paragraph with market context>",
    "leverage_analysis": "<Analysis paragraph with sector norms>",
    "efficiency_analysis": "<Analysis paragraph with peer comparisons>"
  }},
  "benchmarks_used": {{
    "net_profit_margin_industry_avg": <actual number from search>,
    "roe_industry_avg": <actual number from search>,
    "roa_industry_avg": <actual number from search>,
    "current_ratio_healthy_range": "<range from industry data>",
    "debt_to_equity_healthy_range": "<range from industry data>",
    "data_sources": ["<source 1>", "<source 2>", "<source 3>"]
  }},
  "market_context": {{
    "sector": "<identified sector>",
    "region": "<operating region if identifiable>",
    "competitors": ["<competitor 1>", "<competitor 2>", "<competitor 3>"],
    "industry_trends": "<brief summary of current sector trends from search>"
  }}
}}

Base your analysis on ACTUAL searched data from credible financial sources. If you cannot find specific data for this company's exact sector, use the closest comparable industry data and note the approximation.
"""

    try:
        # Enable Google Search grounding for real-time market data
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[types.Part(text=prompt)],
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            ),
            tools=[{"google_search": {}}]  # Enable live web search
        )
        
        analysis = json.loads(response.text.strip())
        analysis["grounding_enabled"] = True
        analysis["search_performed"] = True
        return analysis
        
    except Exception as e:
        print(f"   ⚠️ Grounding failed, attempting without search...")
        # Fallback without grounding if search fails
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
            analysis["search_performed"] = False
            analysis["note"] = "Analysis based on model knowledge, live search unavailable"
            return analysis
        except Exception as e2:
            return {
                "company": company_ratios.get('company', 'Unknown'),
                "error": f"AI analysis failed: {str(e2)}",
                "grounding_enabled": False,
                "search_performed": False,
                "note": "Falling back to basic benchmarking"
            }


def analyze_pdf_files(pdf_pattern="PDF_files/*.pdf",
                     output_ratios_file="company_ratios.json",
                     output_ai_analysis_file="ai_market_analysis.json"):
    """
    Process PDF files directly and generate AI-powered market analysis.
    
    Args:
        pdf_pattern: Pattern to find PDF files (default: "*.pdf" for all PDFs in current directory)
        output_ratios_file: Path for calculated ratios output
        output_ai_analysis_file: Path for AI market analysis output
    """
    # Find all PDF files
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"⚠️ No PDF files found matching pattern: {pdf_pattern}")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process\n")
    
    all_ratios = []
    all_analyses = []
    
    # Process each PDF
    for pdf_path in pdf_files:
        print(f"\n📄 Processing PDF: {pdf_path}")
        
        # Extract financial data from PDF
        print(f"   ├─ Extracting financial data from PDF...")
        company_data = extract_financial_data_from_pdf(pdf_path)
        
        if "error" in company_data:
            print(f"   └─ ⚠️ Skipping due to extraction error")
            continue
        
        company_name = company_data.get('company', 'Unknown')
        print(f"   ├─ Identified company: {company_name}")
        
        # Calculate ratios
        print(f"   ├─ Calculating financial ratios...")
        ratios = calculate_financial_ratios(company_data)
        all_ratios.append(ratios)
        
        # AI market analysis with live search
        print(f"   ├─ Running AI market analysis with live search...")
        analysis = ai_market_analysis_with_grounding(ratios)
        all_analyses.append(analysis)
        
        if "error" not in analysis:
            search_status = "✓ Live data" if analysis.get('search_performed') else "⚠ Cached data"
            print(f"   └─ ✅ Health Score: {analysis.get('overall_health_score', 'N/A')}/100 ({search_status})")
            print(f"      Grade: {analysis.get('performance_grade', 'N/A')}")
            print(f"      Outlook: {analysis.get('investment_outlook', 'N/A')}")
    
    # Save results
    with open(output_ratios_file, "w", encoding="utf-8") as f:
        json.dump(all_ratios, f, indent=4, ensure_ascii=False)
    
    with open(output_ai_analysis_file, "w", encoding="utf-8") as f:
        json.dump(all_analyses, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ Analysis complete!")
    print(f"   - Financial ratios saved to: {output_ratios_file}")
    print(f"   - AI market analysis saved to: {output_ai_analysis_file}")
    print(f"   - Total companies analyzed: {len(all_ratios)}")


if __name__ == "__main__":
    # Process all PDF files in the current directory
    analyze_pdf_files()
