from flask import Flask, request, send_file, jsonify
import pdfkit
import os
import tempfile
from io import BytesIO

app = Flask(__name__)

# Configure pdfkit options
PDF_OPTIONS = {
    'enable-local-file-access': None
}

@app.route('/')
def index():
    return '''
    <!doctype html>
    <title>HTML to PDF Converter</title>
    <h1>Upload HTML File to Convert to PDF</h1>
    <form method=post enctype=multipart/form-data action="/convert">
      <input type=file name=html_file>
      <input type=submit value=Convert>
    </form>
    '''

@app.route('/convert', methods=['POST'])
def convert_html_to_pdf():
    if 'html_file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['html_file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        try:
            # Save the uploaded HTML file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_html:
                file.save(tmp_html.name)
                html_path = tmp_html.name

            # Define the path for the output PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                pdf_path = tmp_pdf.name

            # Convert HTML to PDF
            pdfkit.from_file(html_path, pdf_path, options=PDF_OPTIONS)

            # Send the PDF file as a response
            return send_file(pdf_path, as_attachment=True, download_name='converted.pdf', mimetype='application/pdf')

        except Exception as e:
            return jsonify({'error': str(e)}), 500

        finally:
            # Clean up temporary files
            if os.path.exists(html_path):
                os.remove(html_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    else:
        return jsonify({'error': 'Invalid file type. Only HTML files are allowed.'}), 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'html', 'htm'}

# New API Endpoint for n8n Integration
@app.route('/api/convert', methods=['POST'])
def api_convert():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    html_content = data.get('html')
    if not html_content:
        return jsonify({'error': 'Missing "html" in request body'}), 400

    try:
        # Convert HTML string to PDF in memory
        pdf_bytes = pdfkit.from_string(html_content, False, options=PDF_OPTIONS)

        # Return the PDF as a response
        return send_file(
            BytesIO(pdf_bytes),
            as_attachment=True,
            download_name='converted.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)