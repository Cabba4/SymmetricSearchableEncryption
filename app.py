from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import CSRFProtect
from werkzeug.utils import secure_filename
import os
import hashlib
from database import encrypt_and_store_file, search_encrypted_data, clear_tables # Functions from database.py

app = Flask(__name__)
app.secret_key = os.urandom(32)
csrf = CSRFProtect(app)

# App Config
app.config.update(
    UPLOAD_FOLDER='textfiles',
    ALLOWED_EXTENSIONS={'txt'},
    MAX_CONTENT_LENGTH=1 * 1024 * 1024,  # 1 MB
)


INDEX_PAGE = 'index.html'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template(INDEX_PAGE)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    up_file = request.files['file']
    if up_file and allowed_file(up_file.filename):
        filename = secure_filename(up_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        up_file.save(filepath)

        # Generate KSKE key when file is uploaded
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        combined = f"{ip_address}-{user_agent}"
        kske_key = hashlib.sha256(combined.encode()).digest()

        # Encrypt and store the file using generated KSKE
        encrypt_and_store_file(filepath, kske_key)

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
        return render_template(INDEX_PAGE, message="Word not found.")

    return render_template(INDEX_PAGE, results=results)

@app.route('/clear_tables', methods=['POST'])
def clear_database():
    clear_tables()        # clear the tables
    return redirect('/')  # Redirect back to the main page

if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=5000)

