from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import PyPDF2
import io
import os

app = Flask(__name__)
CORS(app)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not ANTHROPIC_API_KEY:
        return jsonify({'error': 'API key not configured on server'}), 500

    data = request.json
    messages = data.get('messages', [])
    system = data.get('system', '')

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 1000,
                'system': system,
                'messages': messages
            },
            timeout=30
        )
        result = response.json()
        if 'error' in result:
            return jsonify({'error': result['error'].get('message', 'Anthropic API error')}), 500
        return jsonify(result)
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/read-pdf', methods=['POST'])
def read_pdf():
    data = request.json
    file_id = data.get('fileId')
    access_token = data.get('accessToken')

    if not file_id or not access_token:
        return jsonify({'error': 'Missing fileId or accessToken'}), 400

    try:
        url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            return jsonify({'error': 'Could not fetch file from Drive'}), 400

        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)

        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
            if len(text) > 6000:
                break

        return jsonify({'content': text[:6000], 'pages': len(reader.pages)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    key_status = 'configured' if ANTHROPIC_API_KEY else 'MISSING'
    return jsonify({'status': 'ok', 'agent': 'Mr. Ofori 007 School Cloud', 'api_key': key_status})


if __name__ == '__main__':
    app.run(debug=False)
