from flask import Flask, render_template, request, redirect, session
import sqlite3
import unicodedata

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'

# ---------- HELPER: MAKE TEXT SEARCHABLE ----------
def make_searchable(text):
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in text if not unicodedata.combining(c))

# ---------- DATABASE INIT ----------
def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bhajans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            search_title TEXT,
            views INTEGER DEFAULT 0
        )
    ''')
    conn.close()

init_db()

# ---------- HOME ----------
@app.route('/')
def home():
    return render_template('index.html')

# ---------- BHAJAN LIST + SEARCH ----------
@app.route('/bhajans')
def bhajans():
    search_query = request.args.get('search', '')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if search_query:
        search_query_clean = make_searchable(search_query)
        cur.execute("""
            SELECT * FROM bhajans
            WHERE title LIKE ? OR search_title LIKE ?
            ORDER BY id DESC
        """, ('%' + search_query + '%', '%' + search_query_clean + '%'))
    else:
        cur.execute("SELECT * FROM bhajans ORDER BY id DESC")

    bhajans = cur.fetchall()
    conn.close()

    return render_template('bhajans.html', bhajans=bhajans, search_query=search_query)

# ---------- SINGLE BHAJAN ----------
@app.route('/bhajan/<int:id>')
def bhajan(id):
    conn = sqlite3.connect('database.db')
    bhajan = conn.execute("SELECT * FROM bhajans WHERE id=?", (id,)).fetchone()

    conn.execute("UPDATE bhajans SET views = views + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    is_admin = session.get('admin', False)
    return render_template('bhajan.html', bhajan=bhajan, is_admin=is_admin)

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'mahadev123':
            session.clear()
            session['admin'] = True
            return redirect('/admin')
        return "Wrong credentials"
    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------- ADMIN PANEL ----------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('admin') is not True:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        search_title = make_searchable(title)

        conn = sqlite3.connect('database.db')
        conn.execute(
            "INSERT INTO bhajans (title, content, search_title) VALUES (?, ?, ?)",
            (title, content, search_title)
        )
        conn.commit()
        conn.close()
        return redirect('/admin')

    conn = sqlite3.connect('database.db')
    bhajans = conn.execute("SELECT * FROM bhajans ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin.html', bhajans=bhajans)

# ---------- EDIT BHAJAN ----------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if session.get('admin') is not True:
        return redirect('/login')

    conn = sqlite3.connect('database.db')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        search_title = make_searchable(title)

        conn.execute(
            "UPDATE bhajans SET title=?, content=?, search_title=? WHERE id=?",
            (title, content, search_title, id)
        )
        conn.commit()
        conn.close()
        return redirect('/admin')

    bhajan = conn.execute("SELECT * FROM bhajans WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('edit.html', bhajan=bhajan)

# ---------- DELETE BHAJAN ----------
@app.route('/delete/<int:id>')
def delete(id):
    if session.get('admin') is not True:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.execute("DELETE FROM bhajans WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)
