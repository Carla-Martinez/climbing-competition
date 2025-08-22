import streamlit as st
import pandas as pd
import os
from streamlit_autorefresh import st_autorefresh  # Componente necesario

# --- PB iniciales ---
competidores = {
    "Unax": 5.35, "Ivan": 7.149, "Leslie": 6.66, "Leire": 7.32,
    "Haize": 8.67, "Aida": 9.35, "Maria": 7.98, "Alberto": 5.409,
    "Miquel": 5.230, "Alex Rivas": 5.41, "Alejo": 5.47, "Carla": 6.96,
    "Ola": 6.51, "Oriol": 5.47, "Julia": 8.80, "Víctor": 5.97
}

CSV_FILE = "resultados.csv"

def puntuar(pb, tiempo, nuevo_pb):
    dif = abs(tiempo - pb)
    if dif <= 0.1: puntos = 3
    elif dif <= 0.2: puntos = 2
    elif dif <= 0.3: puntos = 1
    else: puntos = 0
    return puntos + (4 if nuevo_pb else 0)

st.title("🏆 Competición de Escalada - Ranking en Vivo")

# Auto-refresco cada 5 segundos
_ = st_autorefresh(interval=5000, key="refresh")

# Carga resultados desde CSV
if os.path.exists(CSV_FILE):
    df_historial = pd.read_csv(CSV_FILE)
    resultados = {nombre: [] for nombre in competidores.keys()}
    for _, row in df_historial.iterrows():
        resultados[row["Competidor"]].append((row["Tipo"], row["Valor"]))
else:
    resultados = {nombre: [] for nombre in competidores.keys()}

# Formulario de entrada
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    nombre = st.selectbox("Escoge competidor", list(competidores.keys()))
with col2:
    opcion = st.radio("Resultado", ["Tiempo", "DNF"], horizontal=True)
with col3:
    tiempo = st.number_input("Nuevo tiempo (s)", min_value=0.0, step=0.01) if opcion == "Tiempo" else None

col4, col5, col6 = st.columns(3)
with col4:
    if st.button("➕ Añadir intento"):
        resultados[nombre].append(("tiempo", tiempo) if opcion == "Tiempo" and tiempo > 0 else ("dnf", None))
        st.success(f"{nombre}: {'tiempo ' + f'{tiempo:.2f}s' if opcion == 'Tiempo' else 'DNF'} añadido")
        rows = [{"Competidor": n, "Tipo": t, "Valor": v} for n, intentos in resultados.items() for t, v in intentos]
        pd.DataFrame(rows).to_csv(CSV_FILE, index=False)

with col5:
    if st.button("↩️ Deshacer último intento"):
        if resultados[nombre]:
            ultimo = resultados[nombre].pop()
            st.info(f"Último intento de {nombre} eliminado ({'DNF' if ultimo[0]=='dnf' else f'{ultimo[1]:.2f}s'})")
            rows = [{"Competidor": n, "Tipo": t, "Valor": v} for n, intentos in resultados.items() for t, v in intentos]
            pd.DataFrame(rows).to_csv(CSV_FILE, index=False)
        else:
            st.error(f"{nombre} no tiene intentos para borrar")

with col6:
    if st.button("🗑️ Borrar historial"):
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
        resultados = {nombre: [] for nombre in competidores.keys()}
        st.info("Historial borrado. Competición reiniciada.")

# Cálculo de ranking
resultados_finales = []
for nombre, pb in competidores.items():
    intentos = resultados[nombre]
    puntos = 0
    mejor = pb
    dnfs = 0
    for tipo, valor in intentos:
        if tipo == "tiempo":
            nuevo_pb = valor < mejor
            if len(intentos) <= 7:
                puntos += puntuar(pb, valor, nuevo_pb)
                mejor = valor if nuevo_pb else mejor
        else:
            dnfs += 1
            if dnfs > 1:
                puntos -= 1

    resultados_finales.append({
        "Competidor": nombre,
        "PB inicial": pb,
        "Intentos": len(intentos),
        "DNFs": dnfs,
        "Puntos": puntos
    })

df = pd.DataFrame(resultados_finales).sort_values(by="Puntos", ascending=False)
st.subheader("📊 Clasificación en Vivo")
st.table(df.reset_index(drop=True))

st.subheader("📜 Historial de intentos")
for nombre, intentos in resultados.items():
    historial = [f"{valor:.2f}s" if t == "tiempo" else "DNF" for t, valor in intentos]
    st.write(f"**{nombre}**: {', '.join(historial) if historial else 'Sin intentos'}")


