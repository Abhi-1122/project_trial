# Instructions for Running the Program

Before running the program, please follow these steps:

1. **Database Setup:**
   - Create a MySQL database named "ISS".
   - Execute the following SQL queries to create the required tables:

   ```sql
   CREATE DATABASE ISS;
   USE ISS;
   CREATE TABLE USER (
       id INT AUTO_INCREMENT PRIMARY KEY,
       username VARCHAR(80) NOT NULL,
       email VARCHAR(120) NOT NULL,
       password VARCHAR(80) NOT NULL
   );

   CREATE TABLE UserImages (
       id INT AUTO_INCREMENT PRIMARY KEY,
       user_id INT,
       image_data LONGBLOB,
       FOREIGN KEY (user_id) REFERENCES USER(id)
   );

2. **Updating Database Connection Details:**

    - Open the Python file named `backend.py`.
    - Navigate to the line containing the database connection details and update your details:

    ```python
    con = pymysql.connect(host='localhost', user="satvik", password="Root@123", db='ISS')
