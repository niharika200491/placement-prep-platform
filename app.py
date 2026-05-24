from flask import Flask,redirect,render_template,url_for,request,session
import sqlite3
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key="niharika"
app.config["SESSION_PERMANANT"]=False
app.config["SESSION TYPE"]="filesystem"
def get_db():
    conn = sqlite3.connect("database.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Python",))
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Java",))
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", ("DBMS",))
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES(?)", ("Aptitude",))
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES(?)",("HTML/CSS",))
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questiontable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        question TEXT NOT NULL UNIQUE,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        correct_option INTEGER,
        difficulty TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
   
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER,
        total_questions INTEGER,
        date_time TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts_details(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER,
        question_id INTEGER,
        selected_option INTEGER,
        is_correct INTEGER,
        FOREIGN KEY (attempt_id) REFERENCES attempts(id),
        FOREIGN KEY (question_id) REFERENCES questiontable(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        difficulty TEXT,
        score INTEGER,
        total INTEGER,
        percentage REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE test_history ADD COLUMN difficulty TEXT")
    except sqlite3.OperationalError:
    # column already exists
        pass
   

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")    

@app.route("/register", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        cnpw=request.form["cpsw"]
        if not name:
            return render_template("register.html",error="Please Enter Name")
        if not email:
            return render_template("register.html",error="Please Enter Email")
        if not password:
            return render_template("register.html",error="Please Enter Password")
        if password!=cnpw:
            return render_template("register.html",error="password doesn't match")
        
        
        
        hashed_password=generate_password_hash(password)
        role = "user"
        
        
        conn = get_db()
        cursor = conn.cursor()

        
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template("register.html",error="Email already registered!")
        


        cursor.execute(
            "INSERT INTO users (name, email, password,role) VALUES (?, ?, ?,?)",
            (name, email, hashed_password,role)
        )

        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()
        session["user_id"] = user[0]
        session["user_name"] = user[1]
        
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        #conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html",error="Invalid Email or Password")
    return render_template("login.html")
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):

            if user[4] != "admin":
                return "Access Denied"

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["role"] = user[4]

            return redirect(url_for("admin_dashboard"))

        else:
            return render_template("admin_login.html",error="Invalid Email or Password")

    return render_template("admin_login.html")
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))


    return render_template("dashboard.html", name=session["user_name"])
@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("admin_login"))
    if session["role"] != "admin":
        return "Access Denied"
    conn=get_db()
    cursor=conn.cursor()
    search = request.args.get("search")

    if search:
        cursor.execute(
        """
        SELECT id,name,email,role
        FROM users
        WHERE role='user'
        AND (name LIKE ? OR email LIKE ?)
        """,
        ('%' + search + '%', '%' + search + '%')
    )

    else:
        cursor.execute(
        "SELECT id,name,email,role FROM users WHERE role='user'")
    users=cursor.fetchall()
    cursor.execute("SELECT count(*) from users")
    total=cursor.fetchone()
    
    conn.close()



    return render_template(
        "admin.html",
        users=users,
        total_c=total[0]
    )
@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "Access Denied"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


@app.route("/start_test",methods=["GET","POST"])
def start_test():
    if request.method=="POST":
        cat=request.form.get("category")
        diff=request.form.get("difficulty")
        session["test_category"] = cat
        session["test_difficulty"] = diff
        conn=get_db()
        cursor=conn.cursor()
        cursor.execute("""SELECT * FROM questiontable WHERE category_id = ? AND difficulty = ? ORDER BY RANDOM() LIMIT 10""", (cat, diff))
        questions = cursor.fetchall()
        conn.close()
        
        return render_template("test.html",questions=questions)
    return render_template("start_test.html")

@app.route("/submit_test", methods=["POST"])
def submit_test():

    score = 0
    total = 0
    wrong_answers = []

    conn = get_db()
    cursor = conn.cursor()

    for key in request.form:

        if key.startswith("q"):

            total += 1
            qid = key[1:]
            user_answer = request.form[key]

            cursor.execute(
                "SELECT question, option1, option2, option3, option4, correct_option FROM questiontable WHERE id=?",
                (qid,)
            )

            row = cursor.fetchone()

            question_text = row[0]
            options = [row[1], row[2], row[3], row[4]]
            correct = row[5]

            if str(user_answer) == str(correct):
                score += 1
            else:
                wrong_answers.append({
                    "question": question_text,
                    "your_answer": options[int(user_answer)-1],
                    "correct_answer": options[int(correct)-1]
                })

    wrong = total - score

    if total > 0:
        percentage = (score * 100) / total
    else:
        percentage = 0
    category = session.get("test_category", "Unknown")  # fallback
    user_id = session.get("user_id")
    difficulty = session.get("test_difficulty", "Unknown")
    cursor.execute("INSERT INTO test_history (difficulty,category, score, total, percentage, user_id) VALUES (?, ?, ?, ?,?,?)",(difficulty,category, score, total, percentage,user_id))

    conn.commit()

    conn.close()

    return render_template(
        "result.html",
        score=score,
        t_q=total,
        w_a=wrong,
        percentage=percentage,
        wrong_answers=wrong_answers
    )
@app.route("/leaderboard/<int:category>")
def leaderboard(category):

    conn = get_db()
    cursor = conn.cursor()

    # top 5 students in this category by percentage
    cursor.execute(
        """SELECT users.name,
       (test_history.score * 100.0 / test_history.total) AS percentage,
       test_history.date
       FROM test_history
       JOIN users ON users.id = test_history.user_id
       WHERE category = ?
       ORDER BY percentage DESC
       LIMIT 5
       """,(category,)
       )
    top_students = cursor.fetchall()
    conn.close()

    return render_template("leaderboard.html", category=category, top_students=top_students)
@app.route("/history")
def history():

    # check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # fetch all test attempts
    cursor.execute("SELECT difficulty,category,score, total, percentage, date FROM test_history WHERE user_id=? ORDER BY date DESC",(session["user_id"],))
    tests = cursor.fetchall()
    

    conn.close()

    return render_template("history.html", tests=tests)
@app.route("/performance")
def performance():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # Total tests attempted
    cursor.execute(
        "SELECT COUNT(*) FROM test_history WHERE user_id=?",
        (user_id,)
    )
    total_tests = cursor.fetchone()[0]

    # Average score
    cursor.execute(
        "SELECT AVG(score) FROM test_history WHERE user_id=?",
        (user_id,)
    )
    avg_score = cursor.fetchone()[0]

    # Best score
    cursor.execute(
        "SELECT MAX(score) FROM test_history WHERE user_id=?",
        (user_id,)
    )
    max_score = cursor.fetchone()[0]

    # Weak category
    cursor.execute("""
        SELECT category, AVG(percentage) as avg_performance
        FROM test_history
        WHERE user_id = ?
        GROUP BY category
        ORDER BY avg_performance ASC
        LIMIT 1
    """, (user_id,))

    weak_category = cursor.fetchone()

    if weak_category:
        weak_category = weak_category[0]
    else:
        weak_category = "No data"

    # Handle None values
    avg_score = avg_score or 0
    max_score = max_score or 0

    conn.close()

    return render_template(
        "performance.html",
        total_tests=total_tests,
        avg_score=round(avg_score, 2),
        best_score=max_score,
        weak_category=weak_category,
        name=session["user_name"]
    )
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



    
if __name__ == "__main__":
    init_db()   
    app.run(debug=True)
