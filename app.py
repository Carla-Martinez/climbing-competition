import streamlit as st
import pandas as pd
import os
import io
from streamlit_autorefresh import st_autorefresh

# --- PB iniciales ---
competidores = {
    "Unax": 5.35, "Ivan": 7.149, "Leslie": 6.66, "Leire": 7.32,
    "Haize": 8.67, "Aida": 9.35, "Maria": 7.98, "Alberto": 5.409,
    "Miquel": 5.230, "Alex Rivas": 5.41, "Alejo": 5.47, "Carla": 6.96,
    "Ola": 6.51, "Oriol": 5.47, "Julia": 8.80, "Víctor": 5.97
}

CSV_FILE = "resultados.csv"

def puntuar(pb_inicial, mejor_tiempo, tiempo_actual):
    # Condición para nuevo PB. Esta es la prioridad más alta.
    if tiempo_actual <= mejor_tiempo:
        return 4
    
    # Si no es un nuevo PB, comprueba si está cerca del PB inicial.
    # El usuario pidió solo "3" o "4" puntos, así que solo consideraremos la mejor cercanía (<=0.1s).
    if abs(tiempo_actual - pb_inicial) <= 0.1:
        return 3
        
    # Si no cumple ninguna de las condiciones anteriores, no hay puntos.
    return 0

st.title("🏆 Competición de Escalada - Ranking en Vivo")

# Inicializa el estado para controlar la visibilidad
if 'show_podium' not in st.session_state:
    st.session_state.show_podium = False

# Auto-refresco cada 5 segundos
_ = st_autorefresh(interval=5000, key="refresh")

# Carga resultados desde CSV con manejo de errores
resultados = {nombre: [] for nombre in competidores.keys()}
if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
    try:
        # Nota: pd.read_csv también debe saber el separador
        df_historial = pd.read_csv(CSV_FILE, sep=';')
        for _, row in df_historial.iterrows():
            resultados[row["Competidor"]].append((row["Tipo"], row["Valor"]))
    except pd.errors.EmptyDataError:
        st.warning("El archivo de resultados está vacío. Creando uno nuevo.")
    except Exception as e:
        st.error(f"Se ha producido un error al cargar el historial: {e}")
        st.info("El historial podría estar corrupto. Se reiniciará la aplicación.")
        os.remove(CSV_FILE)

# Cálculo de ranking para el podio y la clasificación
resultados_finales = []
for nombre, pb in competidores.items():
    intentos = resultados[nombre]
    puntos = 0
    mejor = pb
    dnfs = 0
    for tipo, valor in intentos:
        if tipo == "tiempo":
            # Condición corregida para incluir el mismo tiempo como PB
            
            if len(intentos) <= 7:
                puntos += puntuar(pb, mejor, valor)
                if valor < mejor:
                    mejor = valor
        else:
            dnfs += 1
            if dnfs > 1:
                puntos -= 1

    resultados_finales.append({
        "Competidor": nombre,
        "PB inicial": pb,
        "Intentos": len(intentos),
        "DNFs": dnfs,
        "Puntos": puntos,
        "Mejor tiempo": mejor
    })

# Aquí la tabla se ordena por puntos
df = pd.DataFrame(resultados_finales).sort_values(by="Puntos", ascending=False)

# Si el podio NO está visible, muestra el resto de la interfaz
if not st.session_state.show_podium:
    # Formulario de entrada
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        nombre = st.selectbox("Choose competitor", list(competidores.keys()))
    with col2:
        opcion = st.radio("Result", ["Tiempo", "DNF"], horizontal=True)
    with col3:
        tiempo = st.number_input("Nuevo tiempo (s)", min_value=0.0, step=0.01) if opcion == "Tiempo" else None

    col4, col5, col6, col7, col8 = st.columns(5)

    with col4:
        if st.button("➕ Add attempt"):
            resultados[nombre].append(("tiempo", tiempo) if opcion == "Tiempo" and tiempo > 0 else ("dnf", None))
            st.success(f"{nombre}: {'tiempo ' + f'{tiempo:.2f}s' if opcion == "Tiempo" else 'DNF'} añadido")
            rows = [{"Competidor": n, "Tipo": t, "Valor": v} for n, intentos in resultados.items() for t, v in intentos]
            # Al guardar el CSV, usa ';' como separador
            pd.DataFrame(rows).to_csv(CSV_FILE, index=False, sep=';')

    with col5:
        if st.button("↩️ Undo last attempt"):
            if resultados[nombre]:
                ultimo = resultados[nombre].pop()
                st.info(f"Último intento de {nombre} eliminado ({'DNF' if ultimo[0]=='dnf' else f'{ultimo[1]:.2f}s'})")
                rows = [{"Competidor": n, "Tipo": t, "Valor": v} for n, intentos in resultados.items() for t, v in intentos]
                # Al guardar el CSV, usa ';' como separador
                pd.DataFrame(rows).to_csv(CSV_FILE, index=False, sep=';')
            else:
                st.error(f"{nombre} no tiene intentos para borrar")

    with col6:
        if st.button("🗑️ Clear history"):
            if os.path.exists(CSV_FILE):
                os.remove(CSV_FILE)
            resultados = {nombre: [] for nombre in competidores.keys()}
            st.info("Historial borrado. Competición reiniciada.")

    # --- Lógica para el nuevo botón de descarga ---
    data_to_download = []
    for competidor, intentos in resultados.items():
        pb_inicial = competidores[competidor]
        for i, (tipo, valor) in enumerate(intentos):
            puntos_intento = 0
            if tipo == "tiempo":
                puntos_intento = puntuar(pb_inicial, valor, valor < pb_inicial)
            
            data_to_download.append({
                "Competidor": competidor,
                "PB Inicial": pb_inicial,
                "Intento": i + 1,
                "Tipo de Intento": tipo,
                "Tiempo (s)": f"{valor:.2f}" if valor else "N/A",
                "Puntos por Intento": puntos_intento
            })

    df_download = pd.DataFrame(data_to_download)

    # Al crear el archivo para descargar, usa ';' como separador
    csv_string = df_download.to_csv(index=False, sep=';')
    csv_buffer = io.StringIO(csv_string)

    with col7:
        st.download_button(
            label="⬇️ Download history",
            data=csv_buffer.getvalue().encode('utf-8'),
            file_name='historial_escalada.csv',
            mime='text/csv',
        )

    # Botón para ver el podio
    with col8:
        if st.button("🏅 View podium"):
            st.session_state.show_podium = True
            
    # Función para colorear solo la primera, segunda y tercera fila de la tabla
    def highlight_top_three_by_rank(row):
        rank = df.index.get_loc(row.name)  # Obtiene la posición de la fila en el DataFrame ordenado
        styles = [''] * len(row)

        if rank == 0:
            styles = ['background-color: rgba(255, 215, 0, 0.4)'] * len(row) # Oro
        elif rank == 1:
            styles = ['background-color: rgba(192, 192, 192, 0.4)'] * len(row) # Plata
        elif rank == 2:
            styles = ['background-color: rgba(205, 127, 50, 0.4)'] * len(row) # Bronce
        
        return styles

    st.subheader("📊 Clasificación en Vivo")
    # Usa st.dataframe y el estilo para aplicar los colores
    st.dataframe(df.style.apply(highlight_top_three_by_rank, axis=1), use_container_width=True)

    st.subheader("📜 Historial de intentos")
    for nombre, intentos in resultados.items():
        historial = [f"{valor:.2f}s" if t == "tiempo" else "DNF" for t, valor in intentos]
        st.write(f"**{nombre}**: {', '.join(historial) if historial else 'Sin intentos'}")
        
# Si el podio está visible, lo muestra
else:
    st.subheader("🏆 Podio")
    # Botón para volver al ranking
    st.button("↩️ Back to ranking", on_click=lambda: st.session_state.update(show_podium=False))
    
    # Limita la tabla a los 3 primeros que tengan al menos 1 intento
    top_3 = df[df['Intentos'] > 0].head(3)
    
    # Prepara los datos para la tabla del podio
    podio_data = []
    for index, row in top_3.iterrows():
        nombre_ganador = row["Competidor"]
        mejor_tiempo = row["Mejor tiempo"]
        
        tiempo_str = f"{mejor_tiempo:.2f}s" if mejor_tiempo != float('inf') else "N/A"

        # Asigna el emoji de medalla según la posición
        if index == 0:
            posicion_str = "🥇 1st Place"
        elif index == 1:
            posicion_str = "🥈 2nd Place"
        elif index == 2:
            posicion_str = "🥉 3rd Place"
        else:
            posicion_str = f"{index + 1}th Place"
        
        podio_data.append({
            "Posición": posicion_str,
            "Nombre": nombre_ganador,
            "Mejor Tiempo": tiempo_str
        })
    
    st.table(pd.DataFrame(podio_data))


