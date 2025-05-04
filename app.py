from flask import Flask, request, redirect, render_template_string, url_for, send_file
import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import tempfile

app = Flask(__name__)
DB_PATH = 'foerdermatrix.db'

# Datenbank initialisieren
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
            input[type=text] { padding: 8px; width: 100%; box-sizing: border-box; }
            input[type=submit] { padding: 10px 20px; background: #28a745; color: #fff; border: none; cursor: pointer; }
            a.button { padding: 5px 10px; background: #dc3545; color: white; text-decoration: none; margin-left: 10px; }
            a.edit { background: #007bff; }
            form { display: flex; flex-direction: column; gap: 10px; max-width: 800px; }
            .form-row { display: flex; gap: 10px; }
            .form-row div { flex: 1; }
        </style>
    </head>
    <body>
        <h1>Förderdaten Badesee Halberstadt</h1>
        <form method="post">
            <div class="form-row">
                <div><label>Quelle:<br><input name="quelle" type="text" required></label></div>
                <div><label>Bereich:<br><input name="bereich" type="text" required></label></div>
            </div>
            <div class="form-row">
                <div><label>Art:<br><input name="art" type="text" required></label></div>
                <div><label>Programm:<br><input name="programm" type="text" required></label></div>
            </div>
            <div><input type="submit" value="Speichern"></div>
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
        <a href="/chart">📊 Grafische Auswertung anzeigen</a> |
        <a href="/export">⬇️ Daten als CSV herunterladen</a>
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
    <br><a href="/">Zurück</a>
    '''
    return render_template_string(html, row=row)

@app.route('/chart')
def chart():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT foerderquelle, COUNT(*) as anzahl FROM foerderdaten GROUP BY foerderquelle", conn)
    conn.close()

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

@app.route('/export')
def export_csv():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM foerderdaten", conn)
    conn.close()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    df.to_csv(tmp.name, index=False)
    tmp.close()

    return send_file(tmp.name, as_attachment=True, download_name='foerderdaten.csv', mimetype='text/csv')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
