# Импортируем инструменты Flask и системные библиотеки
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, re, hashlib, os

# Создаём приложение Flask
app = Flask(__name__)
app.secret_key = 'conf2027'  # Секретный ключ для шифрования сессий (входа)
# Путь к файлу базы данных (лежит рядом с app.py)
DB = os.path.join(os.path.dirname(__file__), 'database.db')


# ============================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# ============================================================
def db():
    """Открывает соединение с базой данных SQLite."""
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row  # Позволяет обращаться к полям по имени (user['login'])
    return c


def hash_pwd(p):
    """Превращает пароль в хеш SHA-256 (для безопасного хранения)."""
    return hashlib.sha256(p.encode()).hexdigest()


def init_db():
    """Создаёт таблицы и заполняет их начальными данными при запуске."""
    c = db()

    # Таблица пользователей
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        fullname TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user')""")

    # Таблица помещений (аудитории, коворкинги и т.д.)
    c.execute("""CREATE TABLE IF NOT EXISTS rooms(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL)""")

    # Таблица статусов заявок
    c.execute("""CREATE TABLE IF NOT EXISTS statuses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL)""")

    # Таблица заявок на бронирование
    c.execute("""CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        status_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        payment TEXT NOT NULL)""")

    # Таблица отзывов (один отзыв на одну заявку)
    c.execute("""CREATE TABLE IF NOT EXISTS reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER UNIQUE NOT NULL,
        text TEXT NOT NULL,
        rating INTEGER NOT NULL)""")

    # --- Заполнение начальными данными (только если таблицы пустые) ---
    if c.execute("SELECT COUNT(*) FROM statuses").fetchone()[0] == 0:
        c.executemany("INSERT INTO statuses(name) VALUES(?)",
                      [('Новая',), ('Мероприятие назначено',), ('Завершено',)])

    if c.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
        c.executemany("INSERT INTO rooms(name,type) VALUES(?,?)", [
            ('Аудитория №1', 'аудитория'),
            ('Аудитория №2', 'аудитория'),
            ('Коворкинг «Точка кипения»', 'коворкинг'),
            ('Кинозал', 'кинозал'),
        ])

    # Создаём администратора (логин: Conf2027, пароль: Demo77)
    if c.execute("SELECT COUNT(*) FROM users WHERE login='Conf2027'").fetchone()[0] == 0:
        c.execute("INSERT INTO users(login,password,fullname,phone,email,role)"
                  " VALUES(?,?,?,?,?,?)",
                  ('Conf2027', hash_pwd('Demo77'), 'Администратор Портал',
                   '8(000)000-00-00', 'admin@conf.rf', 'admin'))

    c.commit() # Сохраняем изменения
    c.close()  # Закрываем соединение


# ============================================================
# МАРШРУТЫ (СТРАНИЦЫ)
# ============================================================

@app.route('/')
def index():
    """Главная страница — сразу перекидывает на вход."""
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации."""
    errors = []
    if request.method == 'POST':
        # Получаем данные из формы
        login    = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        fullname = request.form.get('fullname', '').strip()
        phone    = request.form.get('phone', '').strip()
        email    = request.form.get('email', '').strip()

        # Валидация полей (проверка формата)
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

        # Если ошибок нет — сохраняем в БД
        if not errors:
            c = db()
            try:
                c.execute("INSERT INTO users(login,password,fullname,phone,email)"
                          " VALUES(?,?,?,?,?)",
                          (login, hash_pwd(password), fullname, phone, email))
                c.commit()
                c.close()
                return redirect('/login') # Успех -> на страницу входа
            except sqlite3.IntegrityError:
                errors.append('Логин уже занят')
                c.close()

    return render_template('register.html', errors=errors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница авторизации."""
    errors = []
    if request.method == 'POST':
        login    = request.form.get('login', '').strip()
        password = request.form.get('password', '')

        c = db()
        user = c.execute("SELECT * FROM users WHERE login=?", (login,)).fetchone()
        c.close()

        # Проверяем, что пользователь есть и хеш пароля совпадает
        if user and user['password'] == hash_pwd(password):
            session['user_id'] = user['id']
            session['login']   = user['login']
            session['role']    = user['role']

            # Если админ — в панель, если пользователь — к заявкам
            if user['role'] == 'admin':
                return redirect('/admin')
            return redirect('/requests')

        errors.append('Неверный логин или пароль')

    return render_template('login.html', errors=errors)


@app.route('/logout')
def logout():
    """Выход из системы."""
    session.clear() # Очищаем сессию
    return redirect('/login')


@app.route('/requests')
def requests_list():
    """Список заявок текущего пользователя."""
    if 'user_id' not in session:
        return redirect('/login')

    c = db()
    # Сложный запрос: соединяем заявки, помещения, статусы и отзывы
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


@app.route('/requests/create', methods=['GET', 'POST'])
def request_create():
    """Создание новой заявки."""
    if 'user_id' not in session:
        return redirect('/login')

    errors = []
    c = db()

    if request.method == 'POST':
        room  = request.form.get('room', '').strip()
        date  = request.form.get('start_date', '').strip()
        pay   = request.form.get('payment', '').strip()

        if not room: errors.append('Введите название помещения')
        if not date: errors.append('Введите дату начала')
        if pay not in ('очное', 'СБП'): errors.append('Выберите способ оплаты')

        if not errors:
            r = c.execute("SELECT id, name FROM rooms WHERE name=?", (room,)).fetchone()
            if not r:
                errors.append('Помещение не найдено. Введите название точно как в списке.')
            else:
                # Ищем ID статуса "Новая"
                s = c.execute("SELECT id FROM statuses WHERE name='Новая'").fetchone()
                if not s:
                    errors.append('Статус «Новая» не найден в БД')
                else:
                    # Добавляем заявку
                    c.execute("INSERT INTO requests(user_id,room_id,status_id,start_date,payment)"
                              " VALUES(?,?,?,?,?)",
                              (session['user_id'], r['id'], s['id'], date, pay))
                    c.commit()
                    c.close()
                    return redirect('/requests')

    # Получаем список помещений для подсказок (datalist)
    rooms = c.execute("SELECT name FROM rooms ORDER BY name").fetchall()
    c.close()

    return render_template('request_create.html', errors=errors,
                           rooms=[x['name'] for x in rooms])


@app.route('/requests/<int:rid>/review', methods=['POST'])
def add_review(rid):
    """Добавление отзыва к заявке (доступно только если статус 'Завершено')."""
    if 'user_id' not in session:
        return redirect('/login')

    text = request.form.get('text', '').strip()
    rat  = request.form.get('rating', '').strip()

    c = db()
    # Проверяем, принадлежит ли заявка пользователю и её статус
    row = c.execute("""SELECT st.name AS s FROM requests r
                       JOIN statuses st ON st.id=r.status_id
                       WHERE r.id=? AND r.user_id=?""",
                    (rid, session['user_id'])).fetchone()

    if row and row['s'] == 'Завершено' and text and rat.isdigit() and 1 <= int(rat) <= 5:
        try:
            c.execute("INSERT INTO reviews(request_id,text,rating) VALUES(?,?,?)",
                      (rid, text, int(rat)))
        except sqlite3.IntegrityError:
            # Если отзыв уже есть, то обновляем его
            c.execute("UPDATE reviews SET text=?, rating=? WHERE request_id=?",
                      (text, int(rat), rid))
        c.commit()
    c.close()
    return redirect('/requests')


@app.route('/admin')
def admin_panel():
    """Панель администратора (видны все заявки)."""
    if session.get('role') != 'admin':
        return redirect('/login')

    c = db()
    # Запрос всех заявок с информацией о пользователе и помещении
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

    # Список всех статусов для выпадающего списка
    statuses = c.execute("SELECT id, name FROM statuses ORDER BY id").fetchall()
    c.close()

    return render_template('admin.html',
                           requests=[dict(x) for x in rows],
                           statuses=[dict(x) for x in statuses])


@app.route('/admin/<int:rid>/status', methods=['POST'])
def admin_change_status(rid):
    """Смена статуса заявки администратором."""
    if session.get('role') != 'admin':
        return redirect('/login')

    new_status = request.form.get('status_id', '').strip()

    # Если пришло число — обновляем статус в БД
    if new_status.isdigit():
        c = db()
        c.execute("UPDATE requests SET status_id=? WHERE id=?",
                  (int(new_status), rid))
        c.commit()
        c.close()

    return redirect('/admin')


if __name__ == '__main__':
    init_db() # Подготовка БД
    app.run(host='127.0.0.1', port=8080, debug=True)