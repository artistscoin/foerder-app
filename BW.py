import streamlit as st
import pandas as pd
import sqlite3
import shap
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine
import os

# ----- Konfiguration -----
st.set_page_config(page_title="XAI Klickanalyse", layout="wide")
st.title("📊 XAI-Dashboard zur Klickanalyse")

# ----- Verbindung zur Datenbank (SQLite) -----
db_name = "klickanalyse.db"
engine = create_engine(f"sqlite:///{db_name}")
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# ----- Tabellenstruktur erstellen (falls nicht vorhanden) -----
cursor.execute('''
    CREATE TABLE IF NOT EXISTS klickdaten (
        Uhrzeit INTEGER,
        Plattform TEXT,
        Thema_Score REAL,
        Klicks INTEGER,
        Anomalie INTEGER
    )
''')
conn.commit()

# ----- CSV Upload -----
st.sidebar.header("🔼 CSV-Datei hochladen")
uploaded_file = st.sidebar.file_uploader("Wähle eine CSV-Datei", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Anomalie-Label hinzufügen
    df['Anomalie'] = (df['Klicks'] > 800).astype(int)

    # In Datenbank speichern
    df.to_sql('klickdaten', engine, if_exists='replace', index=False)
    st.success("✅ Daten erfolgreich hochgeladen und gespeichert.")

# ----- Daten aus DB laden -----
df = pd.read_sql("SELECT * FROM klickdaten", conn)

if df.empty:
    st.info("⬅️ Bitte lade zunächst eine CSV-Datei mit Klickdaten hoch.")
    st.stop()

# ----- Datenübersicht -----
st.subheader("📋 Vorschau auf die Daten")
st.dataframe(df.head(10))

# ----- Modelltraining -----
st.subheader("🧠 Klassifikationsmodell und SHAP-Auswertung")

X = pd.get_dummies(df.drop(columns='Anomalie'), drop_first=True)

# Sicherstellen, dass alle Werte numerisch sind
X = X.apply(pd.to_numeric, errors='coerce')
X.fillna(0, inplace=True)

y = df['Anomalie']

X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ----- SHAP-Erklärung (neuer Stil) -----
st.markdown("### 🔍 Wichtigste Einflussfaktoren (SHAP)")
explainer = shap.Explainer(model, X_train)
shap_values = explainer(X_test)

fig_summary = plt.figure()
shap.plots.bar(shap_values, show=False)
st.pyplot(fig_summary)

# ----- Einzelne Vorhersage erklären -----
st.markdown("### 🔎 Einzelne Vorhersage erklären")
row_index = st.slider("Wähle einen Datenpunkt aus", 0, len(X_test) - 1, 0)
st.write(X_test.iloc[row_index])

st.markdown("**SHAP-Werte für diese Vorhersage:**")
fig_force = shap.plots.force(
    shap_values[row_index],
    matplotlib=True,
    show=False
)
plt.tight_layout()
st.pyplot(fig_force)

# ----- Verbindungsende -----
conn.close()