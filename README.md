# Symmetric Searchable Encryption (SSE) with Flask and Docker

This project demonstrates a basic implementation of Symmetric Searchable Encryption (SSE) using Flask for web services and Docker for containerization. Users can upload text files, search through encrypted file contents, and manage stored data using a lightweight SQLite database.

## Features
- Upload multiple files.
- Encrypt files with AES and store encrypted content in the database.
- Search through encrypted content using a keyword search.
- Avoid duplicate file uploads by checking file hashes.
- Web interface to interact with the system.

## Requirements

- Python 3.8+
- Docker (for containerization)

## Installation

### 1. Clone the repository:

```bash
git clone https://github.com/Cabba4/SymmetricSearchableEncryption.git
cd SymmetricSearchableEncryption
```

### 2. Run locally

```bash
pip install -r requirements.txt
```

### 3. Run with docker

```
docker build -t sse-flask-app .
docker run -d -p 5000:5000 sse-flask-app
```

## Usage 

Uploading Files:

- Go to the home page and upload one or more text files.

- The files will be encrypted and stored in the database.

Searching Files:

- Enter a keyword in the search bar to search for that keyword in the uploaded files.

- If the keyword is found in any file, the filename will be displayed in the results.

Clear Data:

- Use the "Clear Data" button on the home page to delete all stored files from the database.