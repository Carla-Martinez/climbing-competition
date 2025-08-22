import streamlit as st
import pandas as pd

# --- PB iniciales ---
competidores = {
    "Unax": 5.35,
    "Ivan": 7.149,
    "Leslie": 6.66,
    "Leire": 7.32,
    "Haize": 8.67,
    "Aida": 9.35,
    "Maria": 7.98,
    "Alberto": 5.409,
    "Miquel": 5.230,
    "Alex Rivas": 5.41,
    "Alejo": 5.47,
    "Carla": 6.96,
    "Ola": 6.51,
    "Oriol": 5.47,
    "Julia": 8.80,
    "Víctor": 5.97
}

# --- Función de puntuación ---
def puntuar(pb, tiempo, nuevo_pb):
    dif = abs(tiempo - pb)
    puntos = 0
    if dif <= 0.1:
        puntos = 3
    elif dif <= 0.2:
        puntos = 2
    elif dif <= 0.3:
        puntos = 1
    else:
        puntos = 0
    if nuevo_pb:
        puntos += 4
    return puntos

st.title("🏆 Competición de Escalada - Ranking en Vivo")

# --- Memoria de resultados ---
if "resultados" not in st.session_state:
    st.session_state.resultados = {nombre: [] for nombre in competidores.keys()}

# --- Entrada dinámica ---
col1, col2, col3 = st.columns([2,2,2])
with col1:
    nombre = st.selectbox("Escoge competidor", list(competidores.keys()))
with col2:
    opcion = st.radio("Resultado", ["Tiempo", "DNF"], horizontal=True)
with col3:
    tiempo = None
    if opcion == "Tiempo":
        tiempo = st.number_input("Nuevo tiempo (s)", min_value=0.0, step=0.01)

col4, col5 = st.columns(2)
with col4:
    if st.button("➕ Añadir intento"):
        if opcion == "Tiempo" and tiempo > 0:
            st.session_state.resultados[nombre].append(("tiempo", tiempo))
            st.success(f"{nombre}: tiempo {tiempo:.2f}s añadido")
        elif opcion == "DNF":
            st.session_state.resultados[nombre].append(("dnf", None))
            st.warning(f"{nombre}: DNF añadido")

with col5:
    if st.button("↩️ Deshacer último intento"):
        if st.session_state.resultados[nombre]:
            ultimo = st.session_state.resultados[nombre].pop()
            st.info(f"Último intento de {nombre} eliminado ({'DNF' if ultimo[0]=='dnf' else f'{ultimo[1]:.2f}s'})")
        else:
            st.error(f"{nombre} no tiene intentos para borrar")

# --- Cálculo de puntos y ranking ---
resultados_finales = []
for nombre, pb in competidores.items():
    intentos = st.session_state.resultados[nombre]
    puntos_totales = 0
    mejor = pb
    dnfs = 0
    for tipo, valor in intentos:
        if tipo == "tiempo":
            nuevo_pb = valor < mejor
            if len(intentos) > 7:
                puntos_totales += 0
            else:
                puntos_totales += puntuar(pb, valor, nuevo_pb)
                if nuevo_pb:
                    mejor = valor
        elif tipo == "dnf":
            dnfs += 1
            penalizacion =  -2   # extensible
            if dnfs == 1:
                puntos_totales += 0
            elif dnfs == 2:
                puntos_totales += -1
            elif dnfs < 8:
                puntos_totales += -2
            elif dnfs > 8:
                puntos_totales += 0
            
    
    resultados_finales.append({
        "Competidor": nombre,
        "PB inicial": pb,
        "Intentos": len(intentos),
        "DNFs": dnfs,
        "Puntos": puntos_totales
    })

df = pd.DataFrame(resultados_finales).sort_values(by="Puntos", ascending=False)

st.subheader("📊 Clasificación en Vivo")
st.table(df.reset_index(drop=True))

# --- Mostrar historial individual ---
st.subheader("📜 Historial de intentos")
for nombre, intentos in st.session_state.resultados.items():
    historial = []
    for tipo, valor in intentos:
        if tipo == "tiempo":
            historial.append(f"{valor:.2f}s")
        else:
            historial.append("DNF")
    st.write(f"**{nombre}**: {', '.join(historial) if historial else 'Sin intentos'}")
