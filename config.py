import os

def Config(object):
	SECERET_KEY = os.environ.get("SECRET_KEY") or "someSecretString"