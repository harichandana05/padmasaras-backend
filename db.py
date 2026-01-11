import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",       # change if needed
        database="padmasaras_db"
    )
