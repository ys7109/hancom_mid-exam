# 한컴5기 중간평가 실기 - Todo 관리 API + 웹 UI
본 프로젝트는 VirtualBox Ubuntu 서버 환경에서 실행하는 것을 기준으로 작성되었습니다.
Flask 서버는 SQLite(todo.db)를 사용하여 Todo 데이터를 저장하고,
별도의 MySQL 서버에 쿼리 로그를 저장합니다.

## 주요 기능

- 회원가입
- 로그인 / 로그아웃
- 할 일 추가: `POST /todos`
- 할 일 조회: `GET /todos`
- 할 일 완료 처리: `PUT /todos/<id>`
- 할 일 삭제: `DELETE /todos/<id>`
- jQuery AJAX 기반 웹 UI
- SQLite DB 자동 생성
- MySQL 로그 DB 및 테이블 자동 생성 시도

## 프로젝트 구조

```text
app.py
todo.db                 # 최초 실행 시 자동 생성
templates/index.html
static/script.js
static/style.css
requirements.txt
README.md
```

## 실행 방법

```bash
git clone <저장소 주소>
cd <프로젝트명>
pip install -r requirements.txt
python app.py
```

브라우저 접속:

```text
http://localhost:5000
```

## 기본 테스트 계정

최초 실행 시 아래 기본 계정 자동 생성

```text
아이디: test
비밀번호: 1234
```

## SQLite 테이블

### member

| 필드 | 설명 |
|---|---|
| idx | 회원 번호 |
| uname | 이름 |
| uid | 아이디 |
| upwd | 비밀번호 |
| datetime | 가입 시간 |

### todolist

| 필드 | 설명 |
|---|---|
| id | 할 일 번호 |
| title | 할 일 제목 |
| uid | 작성자 아이디 |
| completed | 완료 여부 |
| datetime | 작성 시간 |

## MySQL 로그 테이블

앱 실행 시 MySQL 서버에 연결되면 `todo_log_db` 데이터베이스와 `query_log` 테이블 자동 생성

### query_log

| 필드 | 설명 |
|---|---|
| id | 로그 번호 |
| type | 쿼리 첫 단어: select, insert, update, delete |
| sql_text | SQL 구문 전체 |
| datetime | 쿼리 발생 시간 |

## MySQL 기본 설정

```text
host: localhost
user: root
password: 1234
database: todo_log_db
port: 3306
```

환경변수로 변경 가능

Linux/macOS:

```bash
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=1234
export MYSQL_DATABASE=todo_log_db
export MYSQL_PORT=3306
python app.py
```

Windows PowerShell:

```powershell
$env:MYSQL_HOST="localhost"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="1234"
$env:MYSQL_DATABASE="todo_log_db"
$env:MYSQL_PORT="3306"
python app.py
```

MySQL 로그가 필요 없거나 MySQL 서버를 켜지 않은 상태에서 빠르게 실행하려면 로그 저장 off 가능

```powershell
$env:MYSQL_LOG_ENABLED="0"
python app.py
```

### 로그인

```http
POST /api/login
Content-Type: application/json

{
  "uid": "test",
  "upwd": "1234"
}
```

### 할 일 조회

```http
GET /todos
```

### 할 일 추가

```http
POST /todos
Content-Type: application/json

{
  "title": "Flask 과제 완성하기"
}
```

### 할 일 완료 처리

```http
PUT /todos/1
```

### 할 일 삭제

```http
DELETE /todos/1
```

## Git 커밋 예시

최소 3회 이상 커밋 조건을 만족하기 위한 예시입니다.

```bash
git init
git add app.py requirements.txt README.md
git commit -m "init flask project"

git add templates/index.html static/script.js static/style.css
git commit -m "add jquery todo ui"

git add .
git commit -m "add sqlite and mysql query logging"
```

GitHub 저장소 업로드:

```bash
git remote add origin <저장소 주소>
git branch -M main
git push -u origin main
```
