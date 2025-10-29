from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import os
import json

# Import the extraction and analysis functions from your scripts
try:
    from financialDataExtraction import analyze_financials
except Exception:
    analyze_financials = None

try:
    from ai_market_analysis import calculate_financial_ratios, ai_market_analysis_with_grounding
except Exception:
    calculate_financial_ratios = None
    ai_market_analysis_with_grounding = None

app = Flask(__name__, static_folder='.', static_url_path='')

# Directory to store uploaded PDFs
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'PDF_files')
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/extract', methods=['POST'])
def api_extract():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_DIR, filename)
        file.save(save_path)

        if analyze_financials:
            result = analyze_financials(save_path)
            return jsonify({'ok': True, 'extraction': result})
        else:
            return jsonify({'ok': False, 'error': 'analyze_financials not available (import failed)'}), 500

    return jsonify({'error': 'invalid file type'}), 400


@app.route('/api/ratios', methods=['POST'])
def api_ratios():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON payload provided'}), 400

    if calculate_financial_ratios:
        ratios = calculate_financial_ratios(data)
        return jsonify({'ok': True, 'ratios': ratios})
    else:
        return jsonify({'ok': False, 'error': 'calculate_financial_ratios not available (import failed)'}), 500


@app.route('/api/market_analysis', methods=['POST'])
def api_market_analysis():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON payload provided'}), 400

    if ai_market_analysis_with_grounding:
        analysis = ai_market_analysis_with_grounding(data)
        return jsonify({'ok': True, 'analysis': analysis})
    else:
        return jsonify({'ok': False, 'error': 'ai_market_analysis_with_grounding not available (import failed)'}), 500


@app.route('/api/files/<path:filename>', methods=['GET'])
def serve_file(filename):
    # Serve JSON and other static output files from workspace root
    safe_path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(safe_path):
        return send_from_directory(os.path.dirname(__file__), filename)
    abort(404)


if __name__ == '__main__':
    # Run on localhost:5000
    app.run(host='0.0.0.0', port=5000, debug=True)
