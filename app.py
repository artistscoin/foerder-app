from flask import Flask, request, redirect, render_template_string, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'foerdermatrix.db'

# Initialisierung der Datenbank
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
        return redirect(url_for('index'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM foerderdaten")
    rows = c.fetchall()
    conn.close()

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Förderdaten</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }
            h1 { color: #333; }
            table { width: 100%; border-collapse: collapse; background: #fff; }
            th, td { padding: 10px; border: 1px solid #ccc; text-align: left; }
            form { margin-bottom: 20px; }
            input[type=text] { padding: 8px; width: 25%; margin: 5px; }
            input[type=submit] { padding: 8px 12px; background: #28a745; color: #fff; border: none; cursor: pointer; }
            a.button { padding: 5px 10px; background: #dc3545; color: white; text-decoration: none; margin-left: 10px; }
            a.edit { background: #007bff; }
        </style>
    </head>
    <body>
        <h1>Förderdaten Badesee Halberstadt</h1>
        <form method="post">
            Quelle: <input name="quelle" type="text" required>
            Bereich: <input name="bereich" type="text" required>
            Art: <input name="art" type="text" required>
            Programm: <input name="programm" type="text" required>
            <input type="submit" value="Speichern">
        </form>

        <h2>Einträge:</h2>
        <table>
            <tr><th>ID</th><th>Quelle</th><th>Bereich</th><th>Art</th><th>Programm</th><th>Aktionen</th></tr>
            {% for row in rows %}
            <tr>
                {% for col in row[:-1] %}<td>{{ col }}</td>{% endfor %}
                <td>{{ row[-1] }}</td>
                <td>
                    <a href="/edit/{{ row[0] }}" class="button edit">Bearbeiten</a>
                    <a href="/delete/{{ row[0] }}" class="button">Löschen</a>
                </td>
            </tr>
            {% endfor %}
        </table>
        <br>
        <a href="/chart">📊 Grafische Auswertung anzeigen</a>
    </body>
    </html>
    '''
    return render_template_string(html, rows=rows)

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM foerderdaten WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        c.execute("UPDATE foerderdaten SET foerderquelle=?, foerderbereich=?, foerderart=?, programme=? WHERE id=?",
                  (request.form['quelle'], request.form['bereich'], request.form['art'], request.form['programm'], id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    c.execute("SELECT * FROM foerderdaten WHERE id = ?", (id,))
    row = c.fetchone()
    conn.close()

    html = '''
    <h1>Datensatz bearbeiten</h1>
    <form method="post">
        Quelle: <input name="quelle" value="{{ row[1] }}"><br>
        Bereich: <input name="bereich" value="{{ row[2] }}"><br>
        Art: <input name="art" value="{{ row[3] }}"><br>
        Programm: <input name="programm" value="{{ row[4] }}"><br>
        <input type="submit" value="Speichern">
    </form>
    '''
    return render_template_string(html, row=row)

@app.route('/chart')
def chart():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT foerderquelle, COUNT(*) as anzahl FROM foerderdaten GROUP BY foerderquelle", conn)
    conn.close()

    import matplotlib.pyplot as plt
    import io
    import base64

    fig, ax = plt.subplots()
    df.plot(kind='bar', x='foerderquelle', y='anzahl', legend=False, ax=ax)
    ax.set_ylabel('Anzahl Einträge')
    ax.set_title('Förderdaten nach Quelle')
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return f'<h1>Auswertung</h1><img src="data:image/png;base64,{plot_url}"><br><a href="/">Zurück</a>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
