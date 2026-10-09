-- Приложение к Модулю 4. База данных интернет-магазина
-- ДЭ 09.02.07 «Разработчик веб и мультимедийных приложений», 2027
--
-- Дамп разворачивается в SQLite, MySQL и PostgreSQL без изменений.
-- Значения ключей заданы явно, поэтому автоинкремент не требуется.
--
-- Обратите внимание: имя покупателя и адрес хранятся по частям,
-- состояние заказа — кодом, дата — отметкой времени, а сумма заказа
-- в базе не хранится. Приложение обязано привести эти данные к виду,
-- описанному в файле Прил_4_ОЗ_КИМ_09.02.07-3-2027.pdf.

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id          INTEGER      NOT NULL,
    last_name   VARCHAR(60)  NOT NULL,
    first_name  VARCHAR(60)  NOT NULL,
    middle_name VARCHAR(60),
    email       VARCHAR(120) NOT NULL,
    city        VARCHAR(60)  NOT NULL,
    street      VARCHAR(120) NOT NULL,
    house       VARCHAR(20)  NOT NULL,
    flat        VARCHAR(20),
    PRIMARY KEY (id)
);

CREATE TABLE products (
    id    INTEGER       NOT NULL,
    title VARCHAR(120)  NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE orders (
    id         INTEGER     NOT NULL,
    user_id    INTEGER     NOT NULL,
    status     VARCHAR(20) NOT NULL,
    created_at VARCHAR(19) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE order_items (
    id       INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- покупатели
INSERT INTO users (id, last_name, first_name, middle_name, email, city, street, house, flat) VALUES (1, 'Ковалёв', 'Артём', 'Игоревич', 'kovalev@example.ru', 'Москва', 'Полярная', '31', '12');
INSERT INTO users (id, last_name, first_name, middle_name, email, city, street, house, flat) VALUES (2, 'Северова', 'Дарья', 'Павловна', 'severova@example.ru', 'Санкт-Петербург', 'Лиговский проспект', '104', '7');
INSERT INTO users (id, last_name, first_name, middle_name, email, city, street, house, flat) VALUES (3, 'Ильин', 'Никита', 'Сергеевич', 'ilin@example.ru', 'Казань', 'Баумана', '58', NULL);
INSERT INTO users (id, last_name, first_name, middle_name, email, city, street, house, flat) VALUES (4, 'Гринько', 'Ольга', 'Владимировна', 'grinko@example.ru', 'Новосибирск', 'Кирова', '12', '45');
INSERT INTO users (id, last_name, first_name, middle_name, email, city, street, house, flat) VALUES (5, 'Мамедов', 'Руслан', 'Тофикович', 'mamedov@example.ru', 'Екатеринбург', 'Малышева', '9', '3');

-- товары
INSERT INTO products (id, title, price) VALUES (1, 'Клавиатура механическая', 1990.00);
INSERT INTO products (id, title, price) VALUES (2, 'Мышь беспроводная', 1250.50);
INSERT INTO products (id, title, price) VALUES (3, 'Монитор 27 дюймов', 18990.00);
INSERT INTO products (id, title, price) VALUES (4, 'Наушники накладные', 4300.00);
INSERT INTO products (id, title, price) VALUES (5, 'Веб-камера HD', 2750.25);
INSERT INTO products (id, title, price) VALUES (6, 'Коврик для мыши', 390.00);
INSERT INTO products (id, title, price) VALUES (7, 'Кабель HDMI 2 м', 560.75);
INSERT INTO products (id, title, price) VALUES (8, 'Подставка для ноутбука', 1870.00);

-- заказы
INSERT INTO orders (id, user_id, status, created_at) VALUES (1, 1, 'done', '2026-02-14 10:15:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (2, 2, 'paid', '2026-02-16 18:40:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (3, 1, 'cancelled', '2026-03-02 09:05:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (4, 3, 'new', '2026-03-11 12:30:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (5, 4, 'shipped', '2026-03-19 15:55:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (6, 2, 'done', '2026-04-01 08:20:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (7, 5, 'new', '2026-04-07 20:10:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (8, 3, 'paid', '2026-04-18 11:45:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (9, 4, 'done', '2026-05-05 14:00:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (10, 5, 'shipped', '2026-05-21 16:35:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (11, 1, 'paid', '2026-06-02 19:25:00');
INSERT INTO orders (id, user_id, status, created_at) VALUES (12, 2, 'new', '2026-06-14 07:50:00');

-- позиции заказов
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (1, 1, 1, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (2, 1, 6, 2);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (3, 2, 3, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (4, 2, 7, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (5, 2, 2, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (6, 3, 4, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (7, 4, 2, 2);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (8, 4, 6, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (9, 5, 5, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (10, 5, 8, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (11, 6, 3, 2);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (12, 7, 7, 3);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (13, 8, 1, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (14, 8, 4, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (15, 8, 2, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (16, 9, 8, 2);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (17, 9, 6, 3);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (18, 10, 3, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (19, 10, 5, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (20, 11, 4, 2);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (21, 11, 7, 2);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (22, 12, 1, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (23, 12, 8, 1);
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (24, 12, 5, 2);
