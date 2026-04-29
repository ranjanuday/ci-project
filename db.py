import mysql.connector
import os

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASSWORD", "Uday@123"),
        database="student_db"
    )