#!/usr/bin/env python3

import os
import mysql.connector


DB_CONFIG = {
    'user': os.environ.get('AWS_DB_USER'),
    'password': os.environ.get('AWS_DB_PASSWORD'),
    'host': os.environ.get('AWS_DB_HOST'),
    'port': os.environ.get('AWS_DB_PORT'),
    'database': 'db_posts'
}

def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn


def get_posts(username):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM posts WHERE username = %s ORDER BY date DESC", (username,))
    rows = cursor.fetchall()

    posts = [dict(row) for row in rows]

    return posts


def post(username, text):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO posts (username, text, date) VALUES (%s, %s, NOW())", (username, text))
    conn.commit()

    return True
