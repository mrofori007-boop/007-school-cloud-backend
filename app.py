from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import PyPDF2
import io
import os
import traceback

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not GEMINI_API_KEY:
        return jsonify({'error': 'Gemini API key not configured'}), 500

    try:
        data = request.json
        messages = data.get('messages', [])
        system = data.get('system', '')

        if not messages:
            return jsonify({'error': 'No messages provided'}), 400

        # Build Gemini contents
        contents = []
        for msg in messages:
            role = 'user' if msg['role'] == 'user' else 'model'
            contents.append({'role': role, 'parts': [{'text': msg['content']}]})

        payload = {
            'system_instruction': {'parts': [{'text': system}]},
            'contents': contents,
            'generationConfig': {
                'maxOutputTokens': 1000,
                'temperature': 0.7
            }
        }

        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}'
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Gemini status: {response.status_code}")
        print(f"Gemini response: {response.text[:500]}")
        
        result = response.json()

        if 'error' in result:
            err_msg = result['error'].get('message', 'Gemini API error')
            print(f"Gemini error: {err_msg}")
            return jsonify({'error': err_msg}), 500

        text = result['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'content': [{'type': 'text', 'text': text}]})

    except Exception as e:
        print(f"Exception: {str(e)}")
        traceback.print_exc()
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
    key_status = 'configured' if GEMINI_API_KEY else 'MISSING'
    return jsonify({'status': 'ok', 'agent': 'Mr. Ofori 007 School Cloud', 'gemini_key': key_status})


if __name__ == '__main__':
    app.run(debug=False)
