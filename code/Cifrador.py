#!/usr/bin/env python
from os.path import exists
from cryptography.fernet import Fernet

class Cifrador:
    def __init__(self):
        location="./bin/secret.bin"
        self._key = None
        if exists(location):
            self.load_file(location)
        else:
            self.save_file(location)

    def save_file(self, location):
        if self._key is None:
            self._key = Fernet.generate_key()
        file = open(location, "wb")
        file.write(self._key)
        file.close()

    def load_file(self, location):
        file = open(location, "rb")
        self._key = file.read()
        file.close()

    def decrypt(self, in_data=None):
        if in_data is None:
            return False
        else:
            cipher = Fernet(self._key)
            return cipher.decrypt(in_data.encode('utf-8')).decode('utf-8')

    def encrypt(self, in_data=""):
        if len(in_data) == 0:
            return False
        else:
            cipher = Fernet(self._key)
            return cipher.encrypt(str.encode(in_data,'utf-8')).decode('utf-8')
