import sqlite3
import pickle
import cv2
from PIL import Image
import numpy as np
import os


def getdbConnection():
    conn = sqlite3.connect('faces.db')
    conn.row_factory = sqlite3.Row
    return conn


def createTables():
    conn = getdbConnection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
     ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            file_path TEXT,
            method TEXT,
            encryptionkey TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()


def createFacesTable():
    conn = getdbConnection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            face_data BLOB
        )
    ''')
    conn.commit()
    conn.close()


def validateImageData(data):
    return data.startswith(b'\xff\xd8\xff\xe0')


def saveFace(name, faceData):
    conn = getdbConnection()
    cursor = conn.cursor()
    _, faceImgEncoded = cv2.imencode('.jpg', faceData)
    faceDataBytes = faceImgEncoded.tobytes()
    try:
        faceArray = np.array(faceData)
        cv2.imwrite(f"{name}.jpg", cv2.cvtColor(faceArray, cv2.COLOR_RGB2BGR))
        print("Image saved successfully")
        cursor.execute("INSERT INTO faces (name, face_data) VALUES (?, ?)", (name, faceDataBytes))
        conn.commit()
    except Exception as e:
        print(f"Error saving image: {e}")
    conn.close()


def saveReferenceImage(username, referenceImage, image_index):
    userDir = os.path.join('reference_images', username)
    os.makedirs(userDir, exist_ok=True)
    filePath = os.path.join(userDir, f"{image_index}.jpg")
    cv2.imwrite(filePath, referenceImage)


def loadReferenceImages(username):
    userDir = os.path.join('reference_images', username)
    if not os.path.exists(userDir):
        return []

    imagePaths = [os.path.join(userDir, filename) for filename in os.listdir(userDir) if filename.endswith('.jpg')]
    return [cv2.imread(imagePath) for imagePath in imagePaths]


def captureReferenceImage(username):
    video = cv2.VideoCapture(0)
    faceCascade = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')

    referenceImagesDir = os.path.join('reference_images', username)
    os.makedirs(referenceImagesDir, exist_ok=True)

    count = 0

    while count < 50:
        ret, frame = video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            crop_img = frame[y:y + h, x:x + w, :]
            cv2.imwrite(os.path.join(referenceImagesDir, f'reference_{count}.jpg'), crop_img)
            print(f"Reference image {count + 1} captured successfully!")
            count += 1

            if count == 50:
                break

        cv2.imshow("Capture Reference Image", frame)
        k = cv2.waitKey(1)
        if k == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()


def saveFilePath(username, file_path, method, key):
    baseDir = 'data/uploads'
    relativePath = os.path.join(username, os.path.basename(file_path))
    conn = getdbConnection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (user_id, filename, file_path, method, encryptionkey) VALUES ((SELECT id FROM users WHERE "
                   "username=?), ?, ?, ?, ?)",
                   (username, os.path.basename(file_path), relativePath, method, key))
    conn.commit()
    conn.close()


def checkUsernameExists(username):
    conn = getdbConnection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def saveUserInfo(username):
    conn = getdbConnection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()


def getFilePath(username, filename):
    conn = getdbConnection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT file_path, method, encryptionkey FROM files WHERE user_id = (SELECT id FROM users WHERE username=?) AND filename = ?",
        (username, filename))
    result = cursor.fetchone()  # Fetch only the single matching row
    conn.close()
    if result:
        baseDir = 'data/uploads'
        filePath, method, key = result
        fullPath = os.path.join(baseDir, filePath)
        fullPath += ".encrypted"
        print(f"File path found for {filename}: {fullPath}")
        return fullPath, method, key
    else:
        print(f"File path not found for {filename}")
        return None


def deleteFileRecord(username, filename):
    user = str(username)
    file = str(filename)
    print(type(user), type(file))
    filePath_result = getFilePath(user, file)
    if filePath_result:
        filePath, method, _ = filePath_result
        if os.path.exists(filePath):
            try:
                # os.remove(filePath)
                # print(f"File {file} deleted successfully!")
                print("Hello")
            except Exception as e:
                print(f"Error deleting file {file}: {e}")
        else:
            print(f"File {file} does not exist at path {filePath}!")
    else:
        print(f"File {file} not found in the database!")
    conn = getdbConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM files WHERE user_id = (SELECT id FROM users WHERE username = ?) AND filename = ?",
                   (user, file))
    except Exception as e:
        print(f"Error deleting file {file}: {e}")
    conn.commit()
    conn.close()
