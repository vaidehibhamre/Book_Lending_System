from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'mysecretkey123!@#'  # Secure key for sessions

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Replace with your MySQL username (e.g., "root")
    password="Root",  # Replace with your MySQL password
    database="library_db"
)
cursor = db.cursor()

# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    print("Admin login route accessed")  # Debug print
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"Attempted login: username={username}, password={password}")  # Debug print
        if username == 'admin' and password == 'admin123':
            session['user_type'] = 'admin'
            print("Login successful, redirecting to admin_dashboard")  # Debug print
            return redirect(url_for('admin_dashboard'))
        else:
            print("Login failed: Invalid credentials")  # Debug print
    return render_template('admin_login.html')

# Student Login
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    print("Student login route accessed")  # Debug print
    if request.method == 'POST':
        prn = request.form['prn']
        cursor.execute("SELECT * FROM Student WHERE PRN = %s", (prn,))
        user = cursor.fetchone()
        if user:
            session['user_type'] = 'student'
            session['prn'] = prn
            print("Student login successful, redirecting to student_dashboard")  # Debug print
            return redirect(url_for('student_dashboard'))
    return render_template('student_login.html')

# Student Signup
@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    print("Student signup route accessed")  # Debug print
    if request.method == 'POST':
        prn = request.form['prn']
        sname = request.form['sname']
        branch = request.form['branch']
        pan = request.form['pan']
        contact = request.form['contact']
        cursor.execute("INSERT INTO Student (PRN, SName, Branch, PAN, Contact_info) VALUES (%s, %s, %s, %s, %s)",
                       (prn, sname, branch, pan, contact))
        db.commit()
        print("Student signup successful, redirecting to student_login")  # Debug print
        return redirect(url_for('student_login'))
    return render_template('student_signup.html')

# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    print(f"Session user_type: {session.get('user_type')}")  # Debug print
    if session.get('user_type') != 'admin':
        print("Access denied: Not an admin")
        return redirect(url_for('admin_login'))
    cursor.callproc('ViewLateFees')
    db.commit()
    cursor.execute("SELECT PRN, Amount FROM Payment WHERE Amount > 0")
    late_fees = cursor.fetchall()
    print("Rendering admin_dashboard.html")
    return render_template('admin_dashboard.html', late_fees=late_fees)

# Add Book
@app.route('/add_book', methods=['POST'])
def add_book():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    author_name = request.form['author_name']
    cursor.callproc('AddBook', (author_name,))
    db.commit()
    print("Book added successfully")
    return redirect(url_for('admin_dashboard'))

# Delete Book
@app.route('/delete_book', methods=['POST'])
def delete_book():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    book_id = request.form['book_id']
    cursor.callproc('DeleteBook', (book_id,))
    db.commit()
    print("Book deleted successfully")
    return redirect(url_for('admin_dashboard'))

# Student Dashboard
@app.route('/student_dashboard')
def student_dashboard():
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    prn = session['prn']
    cursor.execute("SELECT Book_id, author_name, unavailable FROM Book")
    books = cursor.fetchall()
    print("Rendering student_dashboard.html")
    return render_template('student_dashboard.html', books=books, prn=prn)

# Lend Book
@app.route('/lend_book', methods=['POST'])
def lend_book():
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    prn = session['prn']
    book_id = request.form['book_id']
    return_date_str = request.form['return_date']
    return_date = datetime.strptime(return_date_str, '%Y-%m-%d')
    max_return_date = datetime.now() + timedelta(days=60)

    if return_date > max_return_date:
        return "Error: Return date cannot exceed 2 months from today!"
    cursor.execute("SELECT unavailable FROM Book WHERE Book_id = %s", (book_id,))
    availability = cursor.fetchone()
    if availability[0]:
        return "Error: Book is unavailable!"
    cursor.execute("INSERT INTO Borrow (PRN, Book_id, borrow_date, return_date) VALUES (%s, %s, CURDATE(), %s)",
                   (prn, book_id, return_date_str))
    db.commit()
    print("Book lent successfully")
    return redirect(url_for('student_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)