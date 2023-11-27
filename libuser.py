import hashlib
import os
import mysql.connector
from binascii import hexlify, unhexlify
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidKey

HERE = Path(__file__).parent

DB_CONFIG = {
    'user': os.environ.get('AWS_DB_USER'),
    'password': os.environ.get('AWS_DB_PASSWORD'),
    'host': os.environ.get('AWS_DB_HOST'),
    'port': os.environ.get('AWS_DB_PORT'),
    'database': 'db_users'
}

def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn


def login(username, password, **kwargs):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user:
        return False

    backend = default_backend()

    kdf = Scrypt(
        salt=unhexlify(user['salt']),
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=backend
    )

    try:
        kdf.verify(password.encode(), unhexlify(user['password']))
        return username
    except InvalidKey:
        return False

    return False


def user_create(username, password=None):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO users (username, password, salt, failures, mfa_enabled, mfa_secret) VALUES (%s, %s, %s, %s, %s, %s)",
                   (username, '', '', 0, 0, ''))
    conn.commit()

    if password:
        password_set(username, password)

    return True


def password_set(username, password):

    backend = default_backend()
    salt = os.urandom(16)

    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=backend
    )

    key = kdf.derive(password.encode())

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET password = %s, salt = %s WHERE username = %s",
                   (hexlify(key).decode(), hexlify(salt).decode(), username))
    conn.commit()


def userlist():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    return [user['username'] for user in users] if users else []


def password_change(username, old_password, new_password):

    if not login(username, old_password):
        return False

    if not is_password_allowed(new_password):
        return False

    password_set(username, new_password)

    return True


def is_password_complex(password):
    return len(password) >= 12


def is_password_leaked(password):
    with (HERE / 'leaked_passwords.txt').open() as leaked_password_file:
        for p in leaked_password_file.read().split('\n'):
            if password == p:
                return True
    return False


def is_password_allowed(password):
    return is_password_complex(password) and not is_password_leaked(password)
