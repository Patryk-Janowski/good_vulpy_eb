import pyotp
import mysql.connector
from time import sleep
import os

DB_CONFIG = {
    'user': os.environ.get('AWS_DB_USER'),
    'password': os.environ.get('AWS_DB_PASSWORD'),
    'host': os.environ.get('AWS_DB_HOST').split(':')[0],
    'port': os.environ.get('AWS_DB_PORT'),
    'database': 'db_users'
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def mfa_is_enabled(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE username = %s and mfa_enabled = 1", (username, ))
    user = cursor.fetchone()

    conn.close()

    return bool(user)

def mfa_disable(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET mfa_enabled = 0 WHERE username = %s", (username,))
    conn.commit()
    conn.close()

    return True

def mfa_enable(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET mfa_enabled = 1 WHERE username = %s", (username,))
    conn.commit()
    conn.close()

    return True

def mfa_get_secret(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE username = %s", (username, ))
    user = cursor.fetchone()

    conn.close()

    if user:
        return user['mfa_secret']
    else:
        return False

def mfa_reset_secret(username):
    secret = pyotp.random_base32()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET mfa_secret = %s WHERE username = %s", (secret, username))
    conn.commit()
    conn.close()

    return False

def mfa_validate(username, otp):
    secret = mfa_get_secret(username)
    totp = pyotp.TOTP(secret)

    return secret and totp.verify(otp)
