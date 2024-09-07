import cv2
import db_utils


def loadAndPreprocess(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (100, 100))
    return img / 255.0


def saveFacesAndNames(name, faceData):
    conn = db_utils.getdbConnection()
    cursor = conn.cursor()

    for face in faceData:
        _, faceImgEncoded = cv2.imencode('.jpg', face)
        faceDataBytes = faceImgEncoded.tobytes()
        cursor.execute("INSERT INTO faces (name, face_data) VALUES (?, ?)", (name, faceDataBytes))

    conn.commit()
    conn.close()


def signup(name):
    video = cv2.VideoCapture(0)
    facedetect = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')

    faceData = []
    i = 0

    while True:
        ret, frame = video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = facedetect.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cropImg = frame[y:y + h, x:x + w, :]
            cv2.imwrite("temp_cropped_image.jpg", cropImg)
            preprocessedImg = loadAndPreprocess("temp_cropped_image.jpg")
            if len(faceData) <= 100 and i % 10 == 0:
                faceData.append(preprocessedImg)
                db_utils.saveReferenceImage(name, preprocessedImg, i // 10 + 1)
            i = i + 1

            cv2.putText(frame, str(len(faceData)), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 255), 1)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 1)

        cv2.imshow("Sign Up", frame)
        k = cv2.waitKey(1)
        if k == ord('q') or len(faceData) == 100:
            break

    video.release()
    cv2.destroyAllWindows()

    saveFacesAndNames(name, faceData)
    return "Sign up successful!"
