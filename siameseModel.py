import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Layer, Conv2D, Dense, MaxPooling2D, Input, Flatten
from tensorflow.keras.losses import BinaryCrossentropy
import cv2
import os
import numpy as np
from tensorflow.python.keras.utils.generic_utils import custom_object_scope


class L1Dist(Layer):
    def __init__(self, **kwargs):
        super().__init__()

    def call(self, input_embedding, validation_embedding):
        return tf.math.abs(input_embedding - validation_embedding)


def makeEmbedding():
    inputs = Input(shape=(100, 100, 3), name='inputImage')
    x = Conv2D(64, (3, 3), activation='relu')(inputs)
    x = MaxPooling2D(2, 2)(x)
    x = Conv2D(128, (3, 3), activation='relu')(x)
    x = MaxPooling2D(2, 2)(x)
    x = Flatten()(x)
    outputs = Dense(128, activation='sigmoid')(x)
    return Model(inputs, outputs, name='embedding')


def makeSiameseModel():
    inputImage = Input(name='inputImage', shape=(100, 100, 3))
    validationImage = Input(name='validationImage', shape=(100, 100, 3))

    embedding = makeEmbedding()

    inputEmbedding = embedding(inputImage)
    validationEmbedding = embedding(validationImage)

    l1Distance = L1Dist()([inputEmbedding, validationEmbedding])
    outputs = Dense(1, activation='sigmoid')(l1Distance)

    return Model(inputs=[inputImage, validationImage], outputs=outputs, name='SiameseModel')


def preprocess(imagePath):
    img = cv2.imread(imagePath)
    print(os.path.abspath(imagePath))
    img = cv2.resize(img, (100, 100))
    img = img.astype('float32') / 255.0
    img = np.expand_dims(img, axis=0)
    return img

