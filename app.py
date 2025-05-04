from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)
DB_PATH = 'foerdermatrix.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS foerderdaten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            foerderquelle TEXT,
            foerderbereich TEXT,
            foerderart TEXT,
            programme TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    init_db()
    if request.method == 'POST':
        data = (
            request.form['quelle'],
            request.form['bereich'],
            request.form['art'],
            request.form['programm']
        )
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO foerderdaten (foerderquelle, foerderbereich, foerderart, programme) VALUES (?, ?, ?, ?)", data)
        conn.commit()
        conn.close()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM foerderdaten")
    rows = c.fetchall()
    conn.close()

    html = """
    <h1>Förderdaten Badesee Halberstadt</h1>
    <form method="post">
        Quelle: <input name="quelle"><br>
        Bereich: <input name="bereich"><br>
        Art: <input name="art"><br>
        Programm: <input name="programm"><br>
        <input type="submit" value="Speichern">
    </form>
    <h2>Einträge:</h2>
    <table border=1>
        <tr><th>ID</th><th>Quelle</th><th>Bereich</th><th>Art</th><th>Programm</th></tr>
        {% for row in rows %}
        <tr>{% for col in row %}<td>{{ col }}</td>{% endfor %}</tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, rows=rows)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

