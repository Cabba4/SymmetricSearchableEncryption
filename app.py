from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import hashlib
from database import encrypt_and_store_file, search_encrypted_data, clear_tables # Functions from database.py

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'textfiles'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # Generate KSKE key when file is uploaded
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        combined = f"{ip_address}-{user_agent}"
        kske_key = hashlib.sha256(combined.encode()).digest()

        # Encrypt and store the file using generated KSKE
        encrypt_and_store_file(filename, kske_key)

        return redirect(url_for('index'))
    return 'File type not allowed', 400

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')

    # Generate same KSKE key again
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    combined = f"{ip_address}-{user_agent}"

    kske_key = hashlib.sha256(combined.encode()).digest()

    results = search_encrypted_data(query, kske_key)

    if not results:
        return render_template('index.html', message="Word not found.")

    return render_template('index.html', results=results)

@app.route('/clear_tables', methods=['POST'])
def clear_database():
    clear_tables()        # clear the tables
    return redirect('/')  # Redirect back to the main page

if __name__ == "__main__":
    app.run(debug=True)
