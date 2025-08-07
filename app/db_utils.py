import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()  # ✅ Load variables from .env file

def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "chatbot_mysql"),  # ✅ default fallback is good practice
        port=int(os.getenv("DB_PORT", 3306)),        # ✅ include port, even if default
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    return connection
