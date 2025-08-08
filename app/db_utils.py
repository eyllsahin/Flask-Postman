import mysql.connector
import os
import logging
from dotenv import load_dotenv

load_dotenv(override=False)  


logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Get database connection with proper error handling and configuration validation
    """
    
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3308")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    
    
    required_vars = {
        "DB_HOST": db_host,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "DB_NAME": db_name
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        error_msg = f"Missing required database environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        connection = mysql.connector.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=False,
            time_zone='+00:00'
        )
        logger.debug(f"Successfully connected to database at {db_host}:{db_port}")
        return connection
    except mysql.connector.Error as e:
        error_msg = f"Failed to connect to database at {db_host}:{db_port} - {str(e)}"
        logger.error(error_msg)
        raise mysql.connector.Error(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error connecting to database: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e
