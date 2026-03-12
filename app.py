from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import PyPDF2
import io

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

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
        response = requests.get(url, headers=headers)

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
    return jsonify({'status': 'ok', 'agent': 'Mr. Ofori 007 School Cloud'})


if __name__ == '__main__':
    app.run(debug=False)
