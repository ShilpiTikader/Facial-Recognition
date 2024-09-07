import cv2
import os
import numpy as np
from siameseModel import preprocess
from tensorflow.keras.utils import custom_object_scope
import tensorflow as tf
from siameseModel import L1Dist, BinaryCrossentropy


SIAMESE_MODEL_PATH = 'siamesemodel.h5'


# Load the Siamese model
with custom_object_scope({'L1Dist': L1Dist, 'BinaryCrossentropy': BinaryCrossentropy}):
    siamese_Model = tf.keras.models.load_model(SIAMESE_MODEL_PATH)


def verify(model, username, detection_threshold, verification_threshold):
    inputImagePath = os.path.abspath(os.path.join('application_data', 'input_image', 'input_image.jpg'))
    print("Input Image Path:", inputImagePath)

    reference_images_dir = os.path.join('reference_images', username)
    reference_images = [os.path.join(reference_images_dir, image) for image in os.listdir(reference_images_dir)]
    if not reference_images:
        print("Error: No reference images found for user", username)
        return None, False

    results = []
    input_img = preprocess(inputImagePath)
    for reference_image in reference_images:
        validation_img = preprocess(reference_image)

        # Make prediction
        result = model.predict([input_img, validation_img])
        results.append(result)

    # Calculate mean similarity score
    mean_similarity_score = np.mean(results)

    # If the mean similarity score is above the verification threshold, it's the same person
    verified = mean_similarity_score > verification_threshold

    return mean_similarity_score, verified


# Usage example:
# Assuming you have a username for the user being verified

def login(username):
    cap = cv2.VideoCapture(0)
    # faces = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
    while True:
        ret, frame = cap.read()
        faces = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')
        frame = frame[120:120 + 250, 200:200 + 250, :]

        cv2.imshow('Verification', frame)

        # Verification Trigger
        if cv2.waitKey(10) & 0XFF == ord('v'):
            # Save input image to application_data/input_image folder
            cv2.imwrite(os.path.join('application_data', 'input_image', 'input_image.jpg'), frame)
            # Run Verification
            results, verified = verify(siamese_Model, username, 0.65, 0.65)
            return verified

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
