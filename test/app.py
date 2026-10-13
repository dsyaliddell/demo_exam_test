from flask import Flask, render_template, request, redirect, session
import sqlite3, re, hashlib, os
app = Flask(__name__)
app.secret_key = 'conf2027'         
DB = 'database.db'                  


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row       
    return c


def h(p):
    return hashlib.sha256(p.encode()).hexdigest()

def init_db():
    c = db()

    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "login TEXT UNIQUE, password TEXT, fullname TEXT, phone TEXT, email TEXT,"
              "role TEXT DEFAULT 'user')")

    c.execute("CREATE TABLE IF NOT EXISTS rooms(id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "name TEXT, type TEXT)")

    c.execute("CREATE TABLE IF NOT EXISTS statuses(id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "name TEXT)")

    c.execute("CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "user_id INTEGER, room_id INTEGER, status_id INTEGER,"
              "start_date TEXT, payment TEXT)")

    c.execute("CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "request_id INTEGER UNIQUE, text TEXT, rating INTEGER)")

    if c.execute("SELECT COUNT(*) FROM statuses").fetchone()[0] == 0:
        c.executemany("INSERT INTO statuses(name) VALUES(?)",
                      [('Новая',), ('Мероприятие назначено',), ('Завершено',)])

    if c.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
        c.executemany("INSERT INTO rooms(name,type) VALUES(?,?)", [
            ('Аудитория №1', 'аудитория'),
            ('Аудитория №2', 'аудитория'),
            ('Коворкинг', 'коворкинг'),
            ('Кинозал', 'кинозал')])

    if c.execute("SELECT COUNT(*) FROM users WHERE login='Conf2027'").fetchone()[0] == 0:
        c.execute("INSERT INTO users(login,password,fullname,phone,email,role)"
                  " VALUES(?,?,?,?,?,?)",
                  ('Conf2027', h('Demo77'), 'Админ', '8(000)000-00-00', 'a@a.ru', 'admin'))

    c.commit()                        
    c.close()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    err = []

    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        pwd   = request.form.get('password', '')
        name  = request.form.get('fullname', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()


        if not re.fullmatch(r'[A-Za-z0-9]{6,}', login):
            err.append('Логин: латиница и цифры, ≥6')
        if len(pwd) < 8:
            err.append('Пароль: ≥8 символов')
        if not re.fullmatch(r'[А-Яа-яЁё\s]+', name):
            err.append('ФИО: кириллица')
        if not re.fullmatch(r'8\(\d{3}\)\d{3}-\d{2}-\d{2}', phone):
            err.append('Телефон: 8(XXX)XXX-XX-XX')
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            err.append('Email некорректен')


        if not err:
            c = db()
            try:
                c.execute("INSERT INTO users(login,password,fullname,phone,email)"
                          " VALUES(?,?,?,?,?)", (login, h(pwd), name, phone, email))
                c.commit()
                c.close()
                return redirect('/login')               
            except sqlite3.IntegrityError:
                err.append('Логин занят')                
                c.close()

    return render_template('register.html', errors=err)

@app.route('/login', methods=['GET', 'POST'])
def login():
    err = []

    if request.method == 'POST':
        l = request.form.get('login', '').strip()
        p = request.form.get('password', '')

        c = db()
        u = c.execute("SELECT * FROM users WHERE login=?", (l,)).fetchone()
        c.close()

        if u and u['password'] == h(p):
            session['user_id'] = u['id']
            session['login'] = u['login']
            session['role'] = u['role']
            return redirect('/admin' if u['role'] == 'admin' else '/requests')

        err.append('Неверный логин или пароль')

    return render_template('login.html', errors=err)


@app.route('/logout')
def logout():
    session.clear()                                   
    return redirect('/login')


@app.route('/requests')
def requests_list():
    if 'user_id' not in session:                      
        return redirect('/login')

    c = db()
    rows = c.execute("""SELECT r.id, r.start_date, r.payment,
                        rm.name AS room_name, st.name AS status_name,
                        rv.text AS review_text, rv.rating AS review_rating
                        FROM requests r
                        JOIN rooms rm ON rm.id = r.room_id
                        JOIN statuses st ON st.id = r.status_id
                        LEFT JOIN reviews rv ON rv.request_id = r.id
                        WHERE r.user_id = ? ORDER BY r.id DESC""",
                     (session['user_id'],)).fetchall()
    c.close()
    return render_template('requests.html', requests=[dict(x) for x in rows])


@app.route('/requests/create', methods=['GET', 'POST'])
def request_create():
    if 'user_id' not in session:
        return redirect('/login')

    err = []
    c = db()

    if request.method == 'POST':
        room = request.form.get('room', '').strip()
        date = request.form.get('start_date', '').strip()
        pay  = request.form.get('payment', '').strip()

        if not room: err.append('Введите помещение')
        if not date: err.append('Введите дату')
        if pay not in ('очное', 'СБП'): err.append('Выберите оплату')

        if not err:
            r = c.execute("SELECT id FROM rooms WHERE name=?", (room,)).fetchone()
            if not r:
                err.append('Помещение не найдено')
            else:
                s = c.execute("SELECT id FROM statuses WHERE name='Новая'").fetchone()
                c.execute("INSERT INTO requests(user_id,room_id,status_id,start_date,payment)"
                          " VALUES(?,?,?,?,?)",
                          (session['user_id'], r['id'], s['id'], date, pay))
                c.commit()
                c.close()
                return redirect('/requests')

    rooms = c.execute("SELECT name FROM rooms ORDER BY name").fetchall()
    c.close()
    return render_template('request_create.html', errors=err,
                           rooms=[x['name'] for x in rooms])


@app.route('/requests/<int:rid>/review', methods=['POST'])
def add_review(rid):
    if 'user_id' not in session:
        return redirect('/login')

    txt = request.form.get('text', '').strip()
    rat = request.form.get('rating', '').strip()

    c = db()
    row = c.execute("""SELECT st.name AS s FROM requests r
                       JOIN statuses st ON st.id=r.status_id
                       WHERE r.id=? AND r.user_id=?""",
                    (rid, session['user_id'])).fetchone()

    if row and row['s'] == 'Завершено' and txt and rat.isdigit() and 1 <= int(rat) <= 5:
        try:
            c.execute("INSERT INTO reviews(request_id,text,rating) VALUES(?,?,?)",
                      (rid, txt, int(rat)))
        except sqlite3.IntegrityError:
            c.execute("UPDATE reviews SET text=?, rating=? WHERE request_id=?",
                      (txt, int(rat), rid))
        c.commit()
    c.close()
    return redirect('/requests')


@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':                 
        return redirect('/login')

    c = db()
    rows = c.execute("""SELECT r.id, r.start_date, r.payment,
                        u.login AS user_login, u.fullname AS user_name,
                        rm.name AS room_name, st.id AS status_id, st.name AS status_name
                        FROM requests r
                        JOIN users u ON u.id = r.user_id
                        JOIN rooms rm ON rm.id = r.room_id
                        JOIN statuses st ON st.id = r.status_id
                        ORDER BY r.id DESC""").fetchall()

    sts = c.execute("SELECT id, name FROM statuses ORDER BY id").fetchall()
    c.close()
    return render_template('admin.html',
                           requests=[dict(x) for x in rows],
                           statuses=[dict(x) for x in sts])


@app.route('/admin/<int:rid>/status', methods=['POST'])
def admin_change_status(rid):
    if session.get('role') != 'admin':
        return redirect('/login')

    sid = request.form.get('status_id', '').strip()
    if sid.isdigit():
        c = db()
        c.execute("UPDATE requests SET status_id=? WHERE id=?", (int(sid), rid))
        c.commit()
        c.close()
    return redirect('/admin')

if __name__ == '__main__':
    init_db()                                          # создать таблицы
    app.run(host='127.0.0.1', port=8080, debug=True)   # порт 8080