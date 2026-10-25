
import mysql.connector

try:
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="trustvault_db"
    )

    if connection.is_connected():
        print("TrustVault MySQL connection successful!")

    connection.close()

except mysql.connector.Error as error:
    print("Database connection failed:", error)
