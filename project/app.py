# Импортируем инструменты Flask: создание приложения, шаблоны, запросы, редиректы, сессии.
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3      # Встроенная БД в одном файле — не требует установки сервера.
import re           # Регулярные выражения — для проверки логина, телефона, email.
import hashlib      # Хеширование — превращаем пароль в «отпечаток», не храним оригинал.
import os           # Работа с путями к файлам.

# Создаём приложение. __name__ нужен Flask, чтобы найти папки templates/ и static/.
app = Flask(__name__)

# Секретный ключ — для шифрования сессий (памяти о залогиненном пользователе).
app.secret_key = 'conf2027_secret_key_demo'

# Путь к файлу базы. База всегда будет лежать рядом с app.py.
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# ---------- РАБОТА С БАЗОЙ ----------
def get_db():
    """Открывает соединение с SQLite. Если файла нет — создаст."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # Чтобы к полям обращаться по имени: user['login'].
    return conn


def init_db():
    """Создаёт таблицу users при первом запуске."""
    conn = get_db()
    # CREATE TABLE IF NOT EXISTS — создаёт таблицу, если её ещё нет.
    # id — автоинкремент, login/email — уникальны, role — по умолчанию 'user'.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            login     TEXT NOT NULL UNIQUE,
            password  TEXT NOT NULL,
            fullname  TEXT NOT NULL,
            phone     TEXT NOT NULL,
            email     TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'user'
        )
    """)
    conn.commit()   # Без commit() изменения не сохранятся!
    conn.close()


# ---------- ВАЛИДАЦИЯ ----------
def validate_registration(login, password, fullname, phone, email):
    """Проверяет данные. Возвращает список ошибок (пустой = всё ок)."""
    errors = []

    # Логин: только латиница и цифры, минимум 6 символов.
    if not re.fullmatch(r'[A-Za-z0-9]{6,}', login):
        errors.append('Логин: только латиница и цифры, минимум 6 символов')

    # Пароль: минимум 8 символов.
    if len(password) < 8:
        errors.append('Пароль: минимум 8 символов')

    # ФИО: только кириллица и пробелы.
    if not re.fullmatch(r'[А-Яа-яЁё\s]+', fullname):
        errors.append('ФИО: только кириллица и пробелы')

    # Телефон: строго формат 8(XXX)XXX-XX-XX.
    if not re.fullmatch(r'8\(\d{3}\)\d{3}-\d{2}-\d{2}', phone):
        errors.append('Телефон: формат 8(XXX)XXX-XX-XX')

    # Email: простой формат user@domain.zone.
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        errors.append('Email: некорректный формат')

    return errors


def hash_password(password):
    """Превращает пароль в хеш SHA-256 (64 символа)."""
    # encode() — строка → байты, hexdigest() — хеш → строка.
    return hashlib.sha256(password.encode()).hexdigest()


# ---------- МАРШРУТЫ ----------
@app.route('/')
def index():
    """Корень сайта → сразу на страницу входа."""
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация: GET — показать форму, POST — сохранить в базу."""
    errors = []

    if request.method == 'POST':
        # Берём данные из формы, убираем пробелы по краям.
        login    = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        fullname = request.form.get('fullname', '').strip()
        phone    = request.form.get('phone', '').strip()
        email    = request.form.get('email', '').strip()

        # Проверяем данные на ошибки.
        errors = validate_registration(login, password, fullname, phone, email)

        if not errors:
            conn = get_db()
            try:
                # Знаки ? — заглушки, защита от SQL-инъекций.
                # Вместо пароля сохраняем его хеш!
                conn.execute(
                    "INSERT INTO users (login, password, fullname, phone, email) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (login, hash_password(password), fullname, phone, email)
                )
                conn.commit()
                conn.close()
                return redirect(url_for('login'))   # Успех → на страницу входа.
            except sqlite3.IntegrityError:
                # Логин уже есть в базе (нарушено UNIQUE).
                errors.append('Логин уже занят')
                conn.close()

    # GET или POST с ошибками — отдаём шаблон.
    return render_template('register.html', errors=errors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход: GET — показать форму, POST — проверить логин и пароль."""
    errors = []

    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password  = request.form.get('password', '')

        if not login_val or not password:
            errors.append('Заполните все поля')
        else:
            # Ищем пользователя с таким логином.
            conn = get_db()
            user = conn.execute(
                "SELECT * FROM users WHERE login = ?", (login_val,)
            ).fetchone()   # fetchone() — первая запись или None.
            conn.close()

            # Проверяем: пользователь найден И хеш пароля совпадает.
            if user and user['password'] == hash_password(password):
                # Запоминаем пользователя в сессии.
                session['user_id'] = user['id']
                session['login']   = user['login']
                session['role']    = user['role']
                return redirect(url_for('login'))   # Позже заменим на /requests.
            else:
                errors.append('Неверный логин или пароль')

    return render_template('login.html', errors=errors)

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    init_db()   # Создаём таблицу при первом запуске.
    # host='127.0.0.1' — только локально. port=8080 — по требованию КИМ.
    # debug=True — показывать ошибки и авто-перезагружать сервер.
    app.run(host='127.0.0.1', port=8080, debug=True)