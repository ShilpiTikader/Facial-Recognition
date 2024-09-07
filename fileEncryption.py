from cryptography.fernet import Fernet
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
# from Crypto.Protocol.KDF import scrypt
import base64
import hashlib
import os
from Crypto.Util.Padding import pad, unpad  # For PKCS#7 padding


def generate_fernet_key():
    return Fernet.generate_key()


def generate_aes_key():
    key = get_random_bytes(32)
    print("AES key:", key)
    encodedKey = base64.urlsafe_b64encode(key)
    return encodedKey.decode('utf-8')


def encryptFile(filename, key, method="fernet"):
    if method == 'fernet':
        cipherSuite = Fernet(key)
        with open(filename, 'rb') as file:
            plainText = file.read()
        encryptedData = cipherSuite.encrypt(plainText)
        with open(filename + '.encrypted', 'wb') as encryptedFile:
            encryptedFile.write(encryptedData)

    elif method == 'aes':
        with open(filename, 'rb') as file:
            plainText = file.read()
        salt = get_random_bytes(AES.block_size)
        privateKey = hashlib.scrypt(key.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
        cipher = AES.new(privateKey, AES.MODE_GCM)
        cipherText, tag = cipher.encrypt_and_digest(plainText, 'utf-8')
        with open(filename + '.encrypted', 'wb') as encryptedFile:
            [encryptedFile.write(x) for x in (salt, cipher.nonce, tag, cipherText)]
    else:
        raise ValueError("Invalid encryption method")


def decryptFile(encryptedFilename, key, method):
    if method == 'fernet':
        cipherSuite = Fernet(key)
        with open(encryptedFilename, 'rb') as encryptedFile:
            encryptedData = encryptedFile.read()
        decryptedData = cipherSuite.decrypt(encryptedData)

        decryptedFilename = encryptedFilename
        if encryptedFilename.endswith('.encrypted'):
            decryptedFilename = encryptedFilename[:-10]
        else:
            decryptedFilename = encryptedFilename + '.decrypted'

        with open(decryptedFilename, 'wb') as decryptedFile:
            decryptedFile.write(decryptedData)
    elif method == 'aes':
        key = base64.urlsafe_b64decode(key)
        print(type(key))
        print(key)
        with open(encryptedFilename, 'rb') as encryptedFile:
            file_data = encryptedFile.read()

        salt = file_data[:AES.block_size]  # Extract salt (first 16 bytes)
        nonce = file_data[AES.block_size:AES.block_size * 2]  # Extract nonce
        tag = file_data[AES.block_size * 2:AES.block_size * 3]  # Extract tag
        cipherText = file_data[AES.block_size * 3:]  # The rest is ciphertext

        privateKey = hashlib.scrypt(key.decode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=32)
        cipher = AES.new(privateKey, AES.MODE_GCM, nonce=nonce)
        decryptedText = cipher.decrypt_and_verify(cipherText, tag)
        decryptedFilename = encryptedFilename[:-10] if encryptedFilename.endswith('.encrypted') else encryptedFilename + '.decrypted'
        with open(decryptedFilename, 'wb') as decryptedFile:
            decryptedFile.write(decryptedText)
    else:
        raise ValueError("Invalid encryption method")
