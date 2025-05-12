from flask import Flask, render_template, request, redirect, url_for, redirect, url_for, session
import mysql.connector
from tabulate import tabulate
from werkzeug.security import generate_password_hash, check_password_hash
import re
from functools import wraps
app = Flask(__name__)
app.secret_key = '12345678'  

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function



def validate_literature_type(title):
    if not title or len(title.strip()) == 0:
        return False, "Название типа не может быть пустым"
    if len(title) > 100:
        return False, "Название типа слишком длинное (макс. 100 символов)"
    if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-\.\,]+$', title):
        return False, "Название содержит недопустимые символы"
    return True, ""

@app.route("/")
def index():
    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']

        return f'Запрос отправлен методом POST. Имя пользователя {login}, пароль {password}'
    else:
        return render_template('auth.html')

@app.route("/auth", methods=["GET", "POST"])

def auth():
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "").strip()

        if not login or not password:
            return render_template('error.html', message="Логин и пароль не могут быть пустыми")

        db = mysql.connector.connect(
            host="127.127.126.26",
            user="root",
            password="",
            database="LibrarySystem"
        )
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE login = %s", (login,))
        user = cursor.fetchone()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session['user_id'] = user['id']  # Сохраняем ID пользователя в сессии
            session['logged_in'] = True      # Флаг авторизации
            return redirect(url_for('main'))
        else:
            return render_template('error.html', message="Неверный логин или пароль")

    return render_template('auth.html')

@app.route("/logout")
def logout():
    session.clear()  
    return redirect(url_for('auth'))

@app.route("/main")
@login_required
def main():
    conn = mysql.connector.connect(
        host="127.127.126.26",
        user="root",
        password="",
        database="LibrarySystem"
    )
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM TipLiteratury")
    rows = cursor.fetchall()
    column_names = [i[0] for i in cursor.description]

    cursor.close()
    conn.close()

    return render_template("main.html", rows=rows, column_names=column_names)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    search_title = request.form.get("search_title", "").strip()
    
    conn = mysql.connector.connect(
        host="127.127.126.26",
        user="root",
        password="",
        database="LibrarySystem"
    )
    cursor = conn.cursor(dictionary=True)

    if search_title:
        cursor.execute("SELECT id, nazvanie_tipa FROM TipLiteratury WHERE nazvanie_tipa LIKE %s", 
                      (f"%{search_title}%",))
        search_results = cursor.fetchall()
    else:
        search_results = []

    cursor.close()
    conn.close()

    return render_template(
        "search.html",
        search_title=search_title,
        search_results=search_results
    )

@app.route("/db")
@login_required
def exampleDb():
    dbMySql = mysql.connector.connect(
        host='127.127.126.26',
        port=3306,
        user='root',
        password='',
        database='LibrarySystem'
    )  # строка подключения

    cursorMySql = dbMySql.cursor()  # открытие соединения с БД

    query = ("SELECT * FROM Biblioteki")  # шаблон запроса
    cursorMySql.execute(query)  # выполнение запроса
    data = cursorMySql.fetchall()  # получение данных из БД

    dbMySql.close()  # закрытие соединения с БД

    return render_template('db.html', data=data)



@app.route("/insert", methods=["GET", "POST"])
@login_required
def exampleInsertDb():
    dbMySql = mysql.connector.connect(
        host='127.127.126.26',
        port=3306,
        user='root',
        password='',
        database='LibrarySystem'
    )

    cursorMySql = dbMySql.cursor()

    if request.method == "POST":
        query1 = ("INSERT INTO TipLiteratury(nazvanie_tipa) VALUES (%(title)s)")
        cursorMySql.execute(query1, {'title': request.form['title']})
        dbMySql.commit()  

    query2 = ("SELECT * FROM TipLiteratury")
    cursorMySql.execute(query2)
    data = cursorMySql.fetchall()

    dbMySql.close()

    return render_template('db.html', data=data)


@app.route("/delete/<int:id>")
@login_required
def delete(id):
    db = mysql.connector.connect(
        host="127.127.126.26",
        user="root",
        password="",
        database="LibrarySystem"
    )
    cursor = db.cursor()
    cursor.execute("DELETE FROM TipLiteratury WHERE id = %s", (id,))  
    db.commit()
    db.close()
    return redirect(url_for('main'))



@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    db = mysql.connector.connect(
        host="127.127.126.26",
        user="root",
        password="",
        database="LibrarySystem"
    )
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM TipLiteratury WHERE id = %s", (id,))
    row = cursor.fetchone()

    if row is None:
        db.close()
        return render_template('error.html', message="Тип литературы не найден.")

    if request.method == "POST":
        new_title = request.form['title']
        cursor.execute("UPDATE TipLiteratury SET nazvanie_tipa = %s WHERE id = %s", (new_title, id))
        db.commit()
        db.close()
        return redirect(url_for('main'))

    db.close()
    return render_template("edit.html", row=row)




if __name__ == "__main__":
    app.run(debug=True)
