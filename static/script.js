function showMessage(text, isError = false) {
    $('#message').text(text);
    $('#message').css('color', isError ? '#d93025' : '#0b57d0');
}

function checkLogin() {
    $.ajax({
        url: '/api/me',
        method: 'GET',
        success: function (res) {
            if (res.logged_in) {
                $('#authBox').addClass('hidden');
                $('#todoBox').removeClass('hidden');
                $('#userName').text(res.uname);
                loadTodos();
            } else {
                $('#authBox').removeClass('hidden');
                $('#todoBox').addClass('hidden');
            }
        },
        error: function () {
            showMessage('로그인 상태 확인에 실패했습니다.', true);
        }
    });
}

function escapeHtml(text) {
    return $('<div>').text(text).html();
}

function loadTodos() {
    $.ajax({
        url: '/todos',
        method: 'GET',
        success: function (res) {
            $('#todoList').empty();

            if (res.todos.length === 0) {
                $('#todoList').append('<li class="empty">등록된 할 일이 없습니다.</li>');
                return;
            }

            res.todos.forEach(function (todo) {
                const checkedClass = todo.completed ? 'done' : '';
                const completedText = todo.completed ? '완료됨' : '완료';
                const disabled = todo.completed ? 'disabled' : '';
                const safeTitle = escapeHtml(todo.title);

                $('#todoList').append(`
                    <li class="${checkedClass}">
                        <div>
                            <strong>${safeTitle}</strong>
                            <small>${todo.datetime}</small>
                        </div>
                        <div class="actions">
                            <button class="completeBtn" data-id="${todo.id}" ${disabled}>${completedText}</button>
                            <button class="deleteBtn danger" data-id="${todo.id}">삭제</button>
                        </div>
                    </li>
                `);
            });
        },
        error: function (xhr) {
            const msg = xhr.responseJSON ? xhr.responseJSON.message : '목록 조회 실패';
            showMessage(msg, true);
        }
    });
}

$('#registerBtn').on('click', function () {
    $.ajax({
        url: '/api/register',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            uname: $('#regUname').val(),
            uid: $('#regUid').val(),
            upwd: $('#regUpwd').val()
        }),
        success: function (res) {
            showMessage(res.message);
            $('#regUname, #regUid, #regUpwd').val('');
        },
        error: function (xhr) {
            const msg = xhr.responseJSON ? xhr.responseJSON.message : '회원가입 실패';
            showMessage(msg, true);
        }
    });
});

$('#loginBtn').on('click', function () {
    $.ajax({
        url: '/api/login',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            uid: $('#loginUid').val(),
            upwd: $('#loginUpwd').val()
        }),
        success: function (res) {
            showMessage(res.message);
            checkLogin();
        },
        error: function (xhr) {
            const msg = xhr.responseJSON ? xhr.responseJSON.message : '로그인 실패';
            showMessage(msg, true);
        }
    });
});

$('#logoutBtn').on('click', function () {
    $.ajax({
        url: '/api/logout',
        method: 'POST',
        success: function (res) {
            showMessage(res.message);
            checkLogin();
        },
        error: function () {
            showMessage('로그아웃 실패', true);
        }
    });
});

$('#addBtn').on('click', function () {
    $.ajax({
        url: '/todos',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ title: $('#todoTitle').val() }),
        success: function (res) {
            showMessage(res.message);
            $('#todoTitle').val('');
            loadTodos();
        },
        error: function (xhr) {
            const msg = xhr.responseJSON ? xhr.responseJSON.message : '추가 실패';
            showMessage(msg, true);
        }
    });
});

$('#todoTitle').on('keydown', function (e) {
    if (e.key === 'Enter') {
        $('#addBtn').click();
    }
});

$(document).on('click', '.completeBtn', function () {
    const id = $(this).data('id');

    $.ajax({
        url: `/todos/${id}`,
        method: 'PUT',
        success: function (res) {
            showMessage(res.message);
            loadTodos();
        },
        error: function (xhr) {
            const msg = xhr.responseJSON ? xhr.responseJSON.message : '완료 처리 실패';
            showMessage(msg, true);
        }
    });
});

$(document).on('click', '.deleteBtn', function () {
    const id = $(this).data('id');

    $.ajax({
        url: `/todos/${id}`,
        method: 'DELETE',
        success: function (res) {
            showMessage(res.message);
            loadTodos();
        },
        error: function (xhr) {
            const msg = xhr.responseJSON ? xhr.responseJSON.message : '삭제 실패';
            showMessage(msg, true);
        }
    });
});

$(document).ready(function () {
    checkLogin();
});
