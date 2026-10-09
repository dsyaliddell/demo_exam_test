from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, re, hashlib, os

app = Flask(__name__)
app.secret_key = 'conf2027'                              # ключ для сессий
DB = os.path.join(os.path.dirname(__file__), 'database.db')


# ============================================================
# РАБОТА С БД
# ============================================================
def db():
    """Открывает соединение с SQLite."""
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def hash_pwd(p):
    """SHA-256 хеш пароля."""
    return hashlib.sha256(p.encode()).hexdigest()


def init_db():
    """Создаёт все таблицы и начальные данные."""
    c = db()

    # Пользователи
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        fullname TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user')""")

    # Помещения
    c.execute("""CREATE TABLE IF NOT EXISTS rooms(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL)""")

    # Статусы
    c.execute("""CREATE TABLE IF NOT EXISTS statuses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL)""")

    # Заявки
    c.execute("""CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        status_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        payment TEXT NOT NULL)""")

    # Отзывы
    c.execute("""CREATE TABLE IF NOT EXISTS reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER UNIQUE NOT NULL,
        text TEXT NOT NULL,
        rating INTEGER NOT NULL)""")

    # Статусы
    if c.execute("SELECT COUNT(*) FROM statuses").fetchone()[0] == 0:
        c.executemany("INSERT INTO statuses(name) VALUES(?)",
                      [('Новая',), ('Мероприятие назначено',), ('Завершено',)])

    # Помещения
    if c.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
        c.executemany("INSERT INTO rooms(name,type) VALUES(?,?)", [
            ('Аудитория №1', 'аудитория'),
            ('Аудитория №2', 'аудитория'),
            ('Коворкинг «Точка кипения»', 'коворкинг'),
            ('Кинозал', 'кинозал'),
        ])

    # Админ
    if c.execute("SELECT COUNT(*) FROM users WHERE login='Conf2027'").fetchone()[0] == 0:
        c.execute("INSERT INTO users(login,password,fullname,phone,email,role)"
                  " VALUES(?,?,?,?,?,?)",
                  ('Conf2027', hash_pwd('Demo77'), 'Администратор Портал',
                   '8(000)000-00-00', 'admin@conf.rf', 'admin'))

    c.commit()
    c.close()


# ============================================================
# ГЛАВНАЯ
# ============================================================
@app.route('/')
def index():
    return redirect('/login')


# ============================================================
# РЕГИСТРАЦИЯ
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = []
    if request.method == 'POST':
        login    = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        fullname = request.form.get('fullname', '').strip()
        phone    = request.form.get('phone', '').strip()
        email    = request.form.get('email', '').strip()

        if not re.fullmatch(r'[A-Za-z0-9]{6,}', login):
            errors.append('Логин: только латиница и цифры, минимум 6 символов')
        if len(password) < 8:
            errors.append('Пароль: минимум 8 символов')
        if not re.fullmatch(r'[А-Яа-яЁё\s]+', fullname):
            errors.append('ФИО: только кириллица и пробелы')
        if not re.fullmatch(r'8\(\d{3}\)\d{3}-\d{2}-\d{2}', phone):
            errors.append('Телефон: формат 8(XXX)XXX-XX-XX')
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            errors.append('Email: некорректный формат')

        if not errors:
            c = db()
            try:
                c.execute("INSERT INTO users(login,password,fullname,phone,email)"
                          " VALUES(?,?,?,?,?)",
                          (login, hash_pwd(password), fullname, phone, email))
                c.commit()
                c.close()
                return redirect('/login')
            except sqlite3.IntegrityError:
                errors.append('Логин уже занят')
                c.close()

    return render_template('register.html', errors=errors)


# ============================================================
# ВХОД
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == 'POST':
        login    = request.form.get('login', '').strip()
        password = request.form.get('password', '')

        c = db()
        user = c.execute("SELECT * FROM users WHERE login=?", (login,)).fetchone()
        c.close()

        # Проверяем, что пользователь найден И хеш пароля совпадает
        if user and user['password'] == hash_pwd(password):
            session['user_id'] = user['id']
            session['login']   = user['login']
            session['role']    = user['role']

            # Админ → в панель, обычный пользователь → к заявкам
            if user['role'] == 'admin':
                return redirect('/admin')
            return redirect('/requests')

        # Если не нашли или пароль неверный — ошибка
        errors.append('Неверный логин или пароль')

    return render_template('login.html', errors=errors)


# ============================================================
# ВЫХОД
# ============================================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ============================================================
# СПИСОК ЗАЯВОК
# ============================================================
@app.route('/requests')
def requests_list():
    if 'user_id' not in session:
        return redirect('/login')

    c = db()
    rows = c.execute("""
        SELECT r.id, r.start_date, r.payment,
               rm.name AS room_name,
               st.name AS status_name,
               rv.text AS review_text,
               rv.rating AS review_rating
        FROM requests r
        JOIN rooms rm ON rm.id = r.room_id
        JOIN statuses st ON st.id = r.status_id
        LEFT JOIN reviews rv ON rv.request_id = r.id
        WHERE r.user_id = ?
        ORDER BY r.id DESC
    """, (session['user_id'],)).fetchall()
    c.close()

    return render_template('requests.html', requests=[dict(x) for x in rows])


# ============================================================
# СОЗДАНИЕ ЗАЯВКИ (С ОТЛАДКОЙ)
# ============================================================
@app.route('/requests/create', methods=['GET', 'POST'])
def request_create():
    if 'user_id' not in session:
        return redirect('/login')

    errors = []
    c = db()

    if request.method == 'POST':
        room  = request.form.get('room', '').strip()
        date  = request.form.get('start_date', '').strip()
        pay   = request.form.get('payment', '').strip()

        # ==== ОТЛАДКА 1: что пришло из формы ====
        print('=== POST /requests/create ===')
        print('room  =', repr(room))
        print('date  =', repr(date))
        print('pay   =', repr(pay))
        print('user  =', session.get('user_id'))

        # Валидация
        if not room: errors.append('Введите название помещения')
        if not date: errors.append('Введите дату начала')
        if pay not in ('очное', 'СБП'): errors.append('Выберите способ оплаты')

        # ==== ОТЛАДКА 2: какие помещения есть в БД ====
        all_rooms = c.execute("SELECT id, name FROM rooms").fetchall()
        print('Помещения в БД:')
        for x in all_rooms:
            print(f"  id={x['id']}  name={repr(x['name'])}")

        if not errors:
            r = c.execute("SELECT id, name FROM rooms WHERE name=?", (room,)).fetchone()
            # ==== ОТЛАДКА 3: нашлось ли помещение ====
            print('Найдено помещение:', dict(r) if r else None)

            if not r:
                errors.append('Помещение не найдено. Введите название точно как в списке.')
            else:
                s = c.execute("SELECT id FROM statuses WHERE name='Новая'").fetchone()
                print('Статус «Новая»:', dict(s) if s else None)

                if not s:
                    errors.append('Статус «Новая» не найден в БД')
                else:
                    c.execute("INSERT INTO requests(user_id,room_id,status_id,start_date,payment)"
                              " VALUES(?,?,?,?,?)",
                              (session['user_id'], r['id'], s['id'], date, pay))
                    c.commit()
                    c.close()
                    print('✅ Заявка успешно создана')
                    return redirect('/requests')

        # ==== ОТЛАДКА 4: если дошли сюда — что-то не так ====
        print('Ошибки:', errors)

    rooms = c.execute("SELECT name FROM rooms ORDER BY name").fetchall()
    c.close()

    return render_template('request_create.html', errors=errors,
                           rooms=[x['name'] for x in rooms])


# ============================================================
# ОТЗЫВ
# ============================================================
@app.route('/requests/<int:rid>/review', methods=['POST'])
def add_review(rid):
    if 'user_id' not in session:
        return redirect('/login')

    text = request.form.get('text', '').strip()
    rat  = request.form.get('rating', '').strip()

    c = db()
    row = c.execute("""SELECT st.name AS s FROM requests r
                       JOIN statuses st ON st.id=r.status_id
                       WHERE r.id=? AND r.user_id=?""",
                    (rid, session['user_id'])).fetchone()

    if row and row['s'] == 'Завершено' and text and rat.isdigit() and 1 <= int(rat) <= 5:
        try:
            c.execute("INSERT INTO reviews(request_id,text,rating) VALUES(?,?,?)",
                      (rid, text, int(rat)))
        except sqlite3.IntegrityError:
            c.execute("UPDATE reviews SET text=?, rating=? WHERE request_id=?",
                      (text, int(rat), rid))
        c.commit()
    c.close()
    return redirect('/requests')

# ============================================================
# ПАНЕЛЬ АДМИНИСТРАТОРА (задание 1.4)
# ============================================================

@app.route('/admin')
def admin_panel():
    """Панель админа: все заявки всех пользователей."""
    # Проверка: залогинен и роль admin?
    if session.get('role') != 'admin':
        return redirect('/login')

    c = db()
    # JOIN: заявка + пользователь + помещение + статус
    rows = c.execute("""
        SELECT r.id, r.start_date, r.payment,
               u.login     AS user_login,
               u.fullname  AS user_name,
               rm.name     AS room_name,
               st.id       AS status_id,
               st.name     AS status_name
        FROM requests r
        JOIN users u    ON u.id = r.user_id
        JOIN rooms rm   ON rm.id = r.room_id
        JOIN statuses st ON st.id = r.status_id
        ORDER BY r.id DESC
    """).fetchall()

    # Список всех статусов — для выпадающего списка
    statuses = c.execute("SELECT id, name FROM statuses ORDER BY id").fetchall()
    c.close()

    return render_template('admin.html',
                           requests=[dict(x) for x in rows],
                           statuses=[dict(x) for x in statuses])


@app.route('/admin/<int:rid>/status', methods=['POST'])
def admin_change_status(rid):
    """Смена статуса заявки админом."""
    if session.get('role') != 'admin':
        return redirect('/login')

    new_status = request.form.get('status_id', '').strip()

    if new_status.isdigit():
        c = db()
        c.execute("UPDATE requests SET status_id=? WHERE id=?",
                  (int(new_status), rid))
        c.commit()
        c.close()

    return redirect('/admin')


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8080, debug=True)