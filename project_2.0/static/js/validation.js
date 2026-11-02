// Ждём полной загрузки страницы
document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // 1. ВАЛИДАЦИЯ РЕГИСТРАЦИИ
    // ============================================================
    var regForm = document.getElementById('register-form');
    if (regForm) {
        regForm.addEventListener('submit', function (e) {
            var errors = [];
            
            // Получаем значения
            var login = document.getElementById('login').value.trim();
            var pass  = document.getElementById('password').value;
            var name  = document.getElementById('fullname').value.trim();
            var phone = document.getElementById('phone').value.trim();
            var email = document.getElementById('email').value.trim();

            // Проверки по ТЗ
            if (!/^[A-Za-z0-9]{6,}$/.test(login)) errors.push('Логин: латиница и цифры, ≥6');
            if (pass.length < 8) errors.push('Пароль: ≥8 символов');
            if (!/^[А-Яа-яЁё\s]+$/.test(name)) errors.push('ФИО: кириллица и пробелы');
            if (!/^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/.test(phone)) errors.push('Телефон: 8(XXX)XXX-XX-XX');
            if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) errors.push('Email некорректен');

            // Если есть ошибки — блокируем отправку и показываем их
            if (errors.length > 0) {
                e.preventDefault();
                showErrors(regForm, errors, 'reg-errors');
            }
        });
    }

    // ============================================================
    // 2. ВАЛИДАЦИЯ ВХОДА
    // ============================================================
    var loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            var errors = [];
            var login = document.getElementById('login').value.trim();
            var pass  = document.getElementById('password').value;

            // При входе проверяем только, что поля не пустые
            if (!login) errors.push('Введите логин');
            if (!pass) errors.push('Введите пароль');

            if (errors.length > 0) {
                e.preventDefault();
                showErrors(loginForm, errors, 'login-errors');
            }
        });
    }

    // ============================================================
    // 3. ФУНКЦИЯ ВЫВОДА ОШИБОК (общая)
    // ============================================================
    function showErrors(form, errors, containerId) {
        // Удаляем старый блок ошибок, чтобы не дублировались
        var old = document.querySelector('[data-testid="' + containerId + '"]');
        if (old) old.remove();

        // Создаём новый блок
        var div = document.createElement('div');
        div.className = 'errors';
        div.setAttribute('data-testid', containerId); // Атрибут для автотеста
        
        // Формируем список ошибок
        div.innerHTML = '<ul>' + errors.map(function (err) {
            return '<li>' + err + '</li>';
        }).join('') + '</ul>';

        // Вставляем блок перед формой
        form.parentNode.insertBefore(div, form);
    }
});