// Ждём загрузки HTML, чтобы все элементы были на месте
document.addEventListener('DOMContentLoaded', function () {

    var reg = document.getElementById('register-form');

    if (reg) {
        reg.addEventListener('submit', function (e) {
            var err = [];                             

            var l = document.getElementById('login').value.trim();
            var p = document.getElementById('password').value;
            var n = document.getElementById('fullname').value.trim();
            var t = document.getElementById('phone').value.trim();
            var m = document.getElementById('email').value.trim();

            if (!/^[A-Za-z0-9]{6,}$/.test(l))
                err.push('Логин: латиница и цифры, ≥6');

            if (p.length < 8)
                err.push('Пароль: ≥8 символов');

            if (!/^[А-Яа-яЁё\s]+$/.test(n))
                err.push('ФИО: кириллица');

            if (!/^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/.test(t))
                err.push('Телефон: 8(XXX)XXX-XX-XX');

            if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(m))
                err.push('Email некорректен');

            if (err.length) {
                e.preventDefault();                     
                show(reg, err, 'reg-errors');          
            }
        });
    }

    var log = document.getElementById('login-form');

    if (log) {
        log.addEventListener('submit', function (e) {
            var err = [];
            var l = document.getElementById('login').value.trim();
            var p = document.getElementById('password').value;

            if (!l) err.push('Введите логин');
            if (!p) err.push('Введите пароль');

            if (err.length) {
                e.preventDefault();
                show(log, err, 'login-errors');
            }
        });
    }


    function show(form, err, id) {
        var old = document.querySelector('[data-testid="' + id + '"]');
        if (old) old.remove();
        var d = document.createElement('div');
        d.className = 'errors';
        d.setAttribute('data-testid', id);
        d.innerHTML = '<ul>' + err.map(function (x) {
            return '<li>' + x + '</li>';
        }).join('') + '</ul>';

        form.parentNode.insertBefore(d, form);
    }
});