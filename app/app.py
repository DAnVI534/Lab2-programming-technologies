import os
import sqlite3
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "demo-not-secret"

DB_PATH = os.path.join(os.path.dirname(__file__), "lab.db")


def get_db():
    if not hasattr(get_db, "conn"):
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if not exists:
            conn.executescript(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    password TEXT,
                    secret   TEXT
                );
                INSERT INTO users (username, password, secret) VALUES
                    ('admin', 's3cr3t-admin-pw', 'FLAG{admin-only-secret}'),
                    ('alice', 'alicepass',       'личные заметки Алисы');

                CREATE TABLE messages (
                    id   INTEGER PRIMARY KEY,
                    author TEXT,
                    body   TEXT
                );
                INSERT INTO messages (author, body) VALUES
                    ('alice', 'Привет! Это первое сообщение.');
                """
            )
            conn.commit()
        get_db.conn = conn
    return get_db.conn


PAGE = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Эхо</title>
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;color:#e9e9ff;line-height:1.55;
    font-family:'Segoe UI',system-ui,-apple-system,Roboto,Arial,sans-serif;
    background:#0e0b1e;
    background-image:
      radial-gradient(1100px 560px at 82% -12%,rgba(124,92,255,.38),transparent 60%),
      radial-gradient(900px 520px at -12% 112%,rgba(255,92,168,.30),transparent 60%);}}
  a{{color:inherit;text-decoration:none}}
  .wrap{{max-width:760px;margin:0 auto;padding:28px 20px 56px}}
  .topbar{{display:flex;align-items:center;justify-content:space-between;
    gap:12px;flex-wrap:wrap;margin-bottom:26px}}
  .brand{{font-size:22px;font-weight:800;letter-spacing:.3px;
    background:linear-gradient(90deg,#b7a6ff,#ff9ecb);
    -webkit-background-clip:text;background-clip:text;color:transparent}}
  nav{{display:flex;gap:8px}}
  nav a{{padding:8px 15px;border-radius:999px;font-size:14px;color:#cfd0f0;
    background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);transition:.2s}}
  nav a:hover{{background:rgba(124,92,255,.28);border-color:rgba(124,92,255,.55);color:#fff}}
  .card{{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.1);
    border-radius:22px;padding:32px;backdrop-filter:blur(14px);
    box-shadow:0 24px 60px rgba(0,0,0,.45)}}
  h1{{margin:0 0 16px;font-size:30px;font-weight:800}}
  p{{color:#c6c8ee}}
  .tag{{color:#a7aad6;font-size:17px;margin:0 0 26px}}
  .actions{{display:flex;gap:14px;flex-wrap:wrap}}
  .btn{{display:inline-block;padding:13px 22px;border-radius:13px;font-weight:600;cursor:pointer;
    color:#ececff;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.13);transition:.2s}}
  .btn:hover{{transform:translateY(-2px);background:rgba(255,255,255,.12)}}
  .btn-primary{{border:none;color:#fff;background:linear-gradient(90deg,#7c5cff,#ff5ca8);
    box-shadow:0 12px 30px rgba(124,92,255,.42)}}
  .btn-primary:hover{{filter:brightness(1.09)}}
  form{{margin-top:16px}}
  input,textarea{{display:block;width:100%;margin:10px 0;padding:12px 14px;border-radius:12px;
    background:rgba(0,0,0,.26);border:1px solid rgba(255,255,255,.12);color:#fff;font-size:15px;
    outline:none;transition:.2s}}
  input::placeholder,textarea::placeholder{{color:#8e90bd}}
  input:focus,textarea:focus{{border-color:#7c5cff;box-shadow:0 0 0 3px rgba(124,92,255,.25)}}
  textarea{{min-height:92px;resize:vertical}}
  button[type=submit]{{margin-top:6px;padding:12px 24px;border:none;border-radius:12px;
    font-weight:600;font-size:15px;cursor:pointer;color:#fff;
    background:linear-gradient(90deg,#7c5cff,#ff5ca8);box-shadow:0 12px 30px rgba(124,92,255,.38);transition:.2s}}
  button[type=submit]:hover{{transform:translateY(-2px);filter:brightness(1.09)}}
  .msg{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);
    border-left:3px solid #7c5cff;padding:12px 16px;margin:12px 0;border-radius:12px}}
  .msg b{{color:#c9b8ff}}
  footer{{text-align:center;color:#6f7199;font-size:13px;margin-top:28px}}
</style></head>
<body><div class="wrap">
<header class="topbar">
  <a class="brand" href="/">Эхо</a>
  <nav><a href="/login">Вход</a><a href="/guestbook">Гостевая книга</a></nav>
</header>
<main class="card"><h1>{title}</h1>{body}</main>
<footer>Эхо · здесь слышно каждого</footer>
</div></body></html>"""


@app.route("/")
def index():
    return PAGE.format(
        title="Эхо",
        body="<p class='tag'>Скажите что-нибудь — и оно отзовётся в общей ленте. "
        "Коротко, живо, по-человечески.</p>"
        "<div class='actions'>"
        "<a class='btn btn-primary' href='/guestbook'>Открыть ленту</a>"
        "<a class='btn' href='/login'>Войти</a></div>",
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        query = (
            "SELECT * FROM users WHERE username = '%s' AND password = '%s'"
            % (username, password)
        )
        try:
            row = get_db().execute(query).fetchone()
        except sqlite3.Error as exc:
            return PAGE.format(title="Ошибка SQL", body="<pre>%s</pre>"
                               "<p>Запрос: <code>%s</code></p>" % (exc, query))

        if row:
            session["user"] = row["username"]
            return redirect("/dashboard")
        return PAGE.format(title="Вход", body="<p>Неверный логин или пароль.</p>"
                           + _login_form())
    return PAGE.format(title="Вход", body=_login_form())


def _login_form():
    return (
        "<form method='post'>"
        "<input name='username' placeholder='Логин'>"
        "<input name='password' type='password' placeholder='Пароль'>"
        "<button type='submit'>Войти</button></form>"
    )


@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect("/login")
    row = get_db().execute(
        "SELECT secret FROM users WHERE username = ?", (user,)
    ).fetchone()
    secret = row["secret"] if row else "(нет данных)"
    return PAGE.format(
        title="Личный кабинет",
        body="<p>Вы вошли как <b>%s</b>.</p><p>Секрет: <code>%s</code></p>"
        % (user, secret),
    )


@app.route("/guestbook", methods=["GET", "POST"])
def guestbook():
    db = get_db()
    if request.method == "POST":
        author = request.form.get("author", "аноним")
        body = request.form.get("body", "")
        db.execute("INSERT INTO messages (author, body) VALUES (?, ?)", (author, body))
        db.commit()
        return redirect("/guestbook")

    rows = db.execute("SELECT author, body FROM messages ORDER BY id").fetchall()
    items = ""
    for r in rows:
        items += "<div class='msg'><b>%s</b>: %s</div>" % (r["author"], r["body"])

    form = (
        "<form method='post'>"
        "<input name='author' placeholder='Имя'>"
        "<textarea name='body' placeholder='Сообщение'></textarea>"
        "<button type='submit'>Отправить</button></form>"
    )
    return PAGE.format(title="Гостевая книга", body=items + form)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
