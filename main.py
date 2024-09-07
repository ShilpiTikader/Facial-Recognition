from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

import db_utils
from fileEncryption import encryptFile, decryptFile, generate_aes_key, generate_fernet_key
from add_face import signup
from test import login

load_dotenv()
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS')
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'some_secret_key'


def allowedFile(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def getUserUploadDir(username):
    return os.path.join(app.config['UPLOAD_FOLDER'], username)


def ensureUserUploadDirExists(username):
    userUploadDir = getUserUploadDir(username)
    if not os.path.exists(userUploadDir):
        os.makedirs(userUploadDir)


def getUploadedFilenames(username):
    conn = db_utils.getdbConnection()
    cursor = conn.cursor()

    cursor.execute("SELECT filename FROM files WHERE user_id = (SELECT id FROM users WHERE username = ?)",
                   (username,))

    results = cursor.fetchall()
    filenames = [row[0] for row in results]

    conn.close()
    return filenames


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def loginUser():
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            return render_template('login.html', error="Username is required.")
        if db_utils.checkUsernameExists(username) and login(username):
            ensureUserUploadDirExists(username)
            session['username'] = username
            return render_template('welcome.html', username=username, filenames=getUploadedFilenames(username))
        else:
            return render_template('login.html', error="Sorry, you are not authorized!")
    else:
        return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signupUser():
    if request.method == 'POST':
        name = request.form['name']
        if db_utils.checkUsernameExists(name):
            return render_template('signup.html', error="Username already exists.")
        else:
            signup(name)
            db_utils.saveUserInfo(name)
            return render_template('index.html', name=name)
    else:
        return render_template('signup.html')


@app.route('/dashboard', methods=['POST', 'GET'])
def welcome():
    if 'username' in session:
        username = session['username']
        files = getUploadedFilenames(username)
        return render_template('welcome.html', username=username, filenames=files)
    else:
        return redirect(url_for('loginUser'))


@app.route('/upload', methods=['POST'])
def uploadFile():
    if 'username' in session:
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file and allowedFile(file.filename):
            fileName = secure_filename(file.filename)
            userUploadDir = getUserUploadDir(session['username'])
            filePath = os.path.join(userUploadDir, fileName)
            file.save(filePath)

            encryptionLevel = request.form.get('encryption_level')

            if encryptionLevel == 'fernet':
                key = generate_fernet_key()
            elif encryptionLevel == 'aes':
                key = generate_aes_key()
            print(key)
            if key:
                encryptFile(filePath, key)
                os.remove(filePath)

            db_utils.saveFilePath(session['username'], fileName, encryptionLevel, key)

            return redirect(url_for('welcome'))
        else:
            return "Error: File type not allowed."

    else:
        return redirect(url_for('loginUser'))


@app.route('/logout')
def logoutUser():
    session.pop('username', None)
    return redirect(url_for('loginUser'))


@app.route('/delete/<username>/<filename>', methods=['GET'])
def deleteFile(username, filename):
    userUploadDir = getUserUploadDir(username)
    filePath = os.path.join(userUploadDir, filename + '.encrypted')
    print(filePath)
    if os.path.exists(filePath):
        os.remove(filePath)
    db_utils.deleteFileRecord(username, filename)
    return redirect(url_for('welcome'))


@app.route('/download/<username>/<filename>')
def downloadFile(username, filename):
    if 'username' in session:
        # if db_utils.checkFileOwnership(username, filename):
        file_path, method, key = db_utils.getFilePath(username, filename)
        if file_path:
            if not key:
                print("Error: ENCRYPTION_KEY not found in environment variables.")
                return "Error: Encryption key not found."

            try:
                if filename.endswith('.encrypted'):
                    filename = filename[:-10]  # Remove the '.encrypted' suffix
                decryptFile(file_path, key, method)
                decrypted_filename = filename[:-10] if filename.endswith('.encrypted') else filename
                decrypted_filepath = os.path.join(getUserUploadDir(username), decrypted_filename)
                print("Decrypted file path:", decrypted_filepath)

                if os.path.exists(decrypted_filepath):
                    return send_from_directory(getUserUploadDir(username), decrypted_filename, as_attachment=True)
                else:
                    print("Decrypted file not found.")
                    return "Decrypted file not found."
            except Exception as e:
                print(f"Error decrypting file: {e}")
                return "Error decrypting file."
            else:
                return "File not found in database."
        else:
            return "You don't have permission to download this file."
    else:
        return redirect(url_for('loginUser'))


if __name__ == '__main__':
    if not ENCRYPTION_KEY:
        print("Warning: ENCRYPTION_KEY not set. Files will not be encrypted.")
    if not ENCRYPTION_KEY:
        print("Error: ENCRYPTION_KEY not found in environment variables.")
    else:
        print("ENCRYPTION_KEY:", ENCRYPTION_KEY)
    db_utils.createFacesTable()
    db_utils.createTables()
    app.run(debug=True)
