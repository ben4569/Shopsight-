import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB={
    "host":os.getenv("MYSQL_HOST","127.0.0.1"),
    "port":int(os.getenv("MYSQL_PORT","3306")),
    "user":os.getenv("MYSQL_USER","root"),
    "password":os.getenv("MYSQL_PASSWORD",""),
    "database":os.getenv("MYSQL_DATABASE","shopsight")
}

def get_connection():
    return mysql.connector.connect(**DB)
