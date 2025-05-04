import sqlite3
import os
import hashlib
import secrets
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

DB_PATH = os.getenv("SSE_DB_PATH", "./sse_schema.db")

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table with file_name, file_hash, and csp_keyvalue
    cursor.execute('''CREATE TABLE IF NOT EXISTS sse_csp_keywords (
        csp_keywords_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_hash TEXT NOT NULL UNIQUE,  -- Unique hash of the file content
        file_name TEXT NOT NULL,         -- The original name of the file
        csp_keyvalue BLOB NOT NULL       -- Encrypted file content
    )''')

    conn.commit()
    conn.close()


def clear_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='sse_csp_keywords' ''')
    if cursor.fetchone():
        cursor.execute('DELETE FROM sse_csp_keywords')

    conn.commit()
    conn.close()


# Hashing function to get a unique file hash and not upload same file again and again to db
def hash_file(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read the file in chunks of 4K to avoid large file memory issues
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def aes_encrypt(data, key):
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data.encode()) + padder.finalize()

    return iv + encryptor.update(padded_data) + encryptor.finalize()

def aes_decrypt(encrypted_data, key):
    iv = encrypted_data[:16]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
    decryptor = cipher.decryptor()

    decrypted_padded = decryptor.update(encrypted_data[16:]) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(decrypted_padded) + unpadder.finalize()

# Insert or update the encrypted file in the database
def encrypt_and_store_file(file_path, KSKE):
    # Ensure the database and tables are created if they don't exist
    create_db()

    file_hash = hash_file(file_path)  # Generate a unique hash for the file
    file_name = os.path.basename(file_path)  # Get the original file name

    # Check if the file already exists in the database based on the hash
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''SELECT csp_keyvalue FROM sse_csp_keywords WHERE file_hash = ?''', (file_hash,))
    existing_file = cursor.fetchone()

    if existing_file:
        # File already exists, so we don't insert it again
        print("File already exists in the database.")
    else:
        # File doesn't exist, so we encrypt and store it
        with open(file_path, 'rb') as file:
            file_content = file.read(2 * 1024 * 1024) # Max 2mb file read

        encrypted_data = aes_encrypt(file_content.decode(), KSKE)

        # Insert the new file into the database
        cursor.execute('''INSERT INTO sse_csp_keywords (file_hash, file_name, csp_keyvalue) VALUES (?, ?, ?)''', 
                       (file_hash, file_name, encrypted_data))  # Store file hash, file name, and encrypted data

        conn.commit()

    conn.close()


def get_encrypted_file_data(file_hash):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''SELECT csp_keyvalue FROM sse_csp_keywords WHERE file_hash = ?''', (file_hash,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0] if result else None

def search_encrypted_data(query, kske_key):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT file_name, csp_keyvalue FROM sse_csp_keywords')
    rows = cursor.fetchall()

    results = []
    for file_name, encrypted_data in rows:
        try:
            decrypted_data = aes_decrypt(encrypted_data, kske_key)

            if query.lower().encode() in decrypted_data.lower():
                results.append(file_name)  # Return the file name in the results
        except Exception:
            continue

    conn.close()
    return results
