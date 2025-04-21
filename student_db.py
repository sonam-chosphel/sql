from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import sqlite3

# Initialize DB
conn = sqlite3.connect("students.db")
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        email TEXT NOT NULL UNIQUE,
        gender TEXT NOT NULL,
        department TEXT NOT NULL,
        year_of_study INTEGER NOT NULL
    )
""")
conn.commit()
conn.close()

class StudentServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            with open("index.html", "rb") as f:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
        elif self.path.startswith("/view"):
            conn = sqlite3.connect("students.db")
            cur = conn.cursor()
            cur.execute("SELECT * FROM students")
            rows = cur.fetchall()
            conn.close()

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Student Records</h1><table border='1'><tr><th>ID</th><th>Name</th><th>Age</th><th>Email</th><th>Gender</th><th>Dept</th><th>Year</th></tr>")
            for row in rows:
                self.wfile.write(f"<tr>{''.join(f'<td>{col}</td>' for col in row)}</tr>".encode())
            self.wfile.write(b"</table><br><a href='/'>Back to Home</a>")

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        data = urllib.parse.parse_qs(body.decode())

        path = self.path
        conn = sqlite3.connect("students.db")
        cur = conn.cursor()

        try:
            if path == "/add":
                cur.execute("INSERT INTO students (name, age, email, gender, department, year_of_study) VALUES (?, ?, ?, ?, ?, ?)", (
                    data["name"][0], int(data["age"][0]), data["email"][0],
                    data["gender"][0], data["department"][0], int(data["year"][0])
                ))
                message = "Student added successfully!"

            elif path == "/update":
                student_id = int(data["id"][0])
                fields = []
                values = []

                for key in ["name", "age", "email", "gender", "department", "year"]:
                    if key in data and data[key][0]:
                        column = "year_of_study" if key == "year" else key
                        fields.append(f"{column} = ?")
                        values.append(data[key][0])

                if fields:
                    query = f"UPDATE students SET {', '.join(fields)} WHERE id = ?"
                    values.append(student_id)
                    cur.execute(query, values)
                    message = "Student updated successfully!"
                else:
                    message = "No update data provided."

            elif path == "/delete":
                student_id = int(data["id"][0])
                cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
                message = "Student deleted successfully!"

            conn.commit()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h2>{message}</h2><br><a href='/'>Back to Home</a>".encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h2>Error: {str(e)}</h2><br><a href='/'>Back to Home</a>".encode())
        finally:
            conn.close()

if __name__ == "__main__":
    print("Server running at http://localhost:8000")
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, StudentServer)
    httpd.serve_forever()
