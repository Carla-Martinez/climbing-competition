import streamlit as st
import pandas as pd
import os
import io
from streamlit_autorefresh import st_autorefresh

# --- Initial PBs ---
competidores = {
    "Unax": 5.35, "Ivan": 7.149, "Leslie": 6.66, "Leire": 7.32,
    "Haize": 8.67, "Aida": 9.35, "Maria": 7.98, "Alberto": 5.409,
    "Miquel": 5.230, "Alex Rivas": 5.41, "Alejo": 5.47, "Carla": 6.96,
    "Ola": 6.51, "Oriol": 5.47, "Julia": 8.80, "Víctor": 5.97
}

CSV_FILE = "resultados.csv"

def puntuar(pb_inicial, mejor_tiempo, tiempo_actual):
    """
    Calculates points for an attempt.

    Args:
        pb_inicial (float): The competitor's initial personal best (PB).
        mejor_tiempo (float): The competitor's best time up to the current attempt.
        tiempo_actual (float): The time of the current attempt.

    Returns:
        int: The points earned in this attempt.
    """
    # Condition for a new PB.
    if tiempo_actual <= mejor_tiempo:
        return 4
    
    # More detailed scoring logic
    if abs(tiempo_actual - pb_inicial) <= 0.1:
        return 3
    elif abs(tiempo_actual - pb_inicial) <= 0.2:
        return 2
    elif abs(tiempo_actual - pb_inicial) <= 0.5:
        return 1
    
    # If none of the conditions are met, there are no points.
    return 0

st.title("🏆 Climbing Competition - Live Ranking")

# Initializes the state to control visibility and confirmation
if 'show_podium' not in st.session_state:
    st.session_state.show_podium = False
if 'confirm_undo' not in st.session_state:
    st.session_state.confirm_undo = False
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False

# Auto-refresh every 5 seconds
_ = st_autorefresh(interval=5000, key="refresh")

# Loads results from CSV with error handling
resultados = {nombre: [] for nombre in competidores.keys()}
if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
    try:
        df_historial = pd.read_csv(CSV_FILE, sep=';')
        
        # Converts the 'Valor' column to a numeric type to ensure correct comparison
        df_historial['Valor'] = pd.to_numeric(df_historial['Valor'], errors='coerce')
        
        for _, row in df_historial.iterrows():
            resultados[row["Competidor"]].append((row["Tipo"], row["Valor"]))
    except pd.errors.EmptyDataError:
        st.warning("The results file is empty. Creating a new one.")
    except Exception as e:
        st.error(f"An error occurred while loading the history: {e}")
        st.info("The history might be corrupted. The application will restart.")
        os.remove(CSV_FILE)

# Calculates the ranking for the podium and classification
resultados_finales = []
for nombre, pb in competidores.items():
    intentos = resultados[nombre]
    puntos = 0
    mejor = pb
    dnfs = 0
    for tipo, valor in intentos:
        if tipo == "tiempo":
            # Corrects the condition to include the same time as a PB
            if len(intentos) <= 7:
                puntos += puntuar(pb, mejor, valor)
                if valor < mejor:
                    mejor = valor
        else:
            dnfs += 1
            if dnfs > 1:
                puntos -= 1

    resultados_finales.append({
        "Competitor": nombre,
        "Initial PB": pb,
        "Attempts": len(intentos),
        "DNFs": dnfs,
        "Points": puntos,
        "Best time": mejor
    })

# The table is sorted by points
df = pd.DataFrame(resultados_finales).sort_values(by="Points", ascending=False)

# If the podium is NOT visible, show the rest of the interface
if not st.session_state.show_podium:
    # Input form
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        nombre = st.selectbox("Escoge competidor", list(competidores.keys()))
    with col2:
        opcion = st.radio("Resultado", ["Time", "DNF"], horizontal=True)
    with col3:
        tiempo = st.number_input("New time (s)", min_value=0.0, step=0.01) if opcion == "Time" else None

    col4, col5, col6, col7, col8 = st.columns(5)

    with col4:
        if st.button("➕ Add attempt"):
            resultados[nombre].append(("tiempo", tiempo) if opcion == "Time" and tiempo > 0 else ("dnf", None))
            st.success(f"{nombre}: {'time ' + f'{tiempo:.2f}s' if opcion == 'Time' else 'DNF'} added")
            rows = [{"Competidor": n, "Tipo": t, "Valor": v} for n, intentos in resultados.items() for t, v in intentos]
            # When saving the CSV, use ';' as a separator
            pd.DataFrame(rows).to_csv(CSV_FILE, index=False, sep=';')

    with col5:
        # Conditional buttons for Undo confirmation
        if st.session_state.confirm_undo:
            st.warning("Are you sure you want to undo the last attempt?")
            col_confirm_undo, col_cancel_undo = st.columns(2)
            with col_confirm_undo:
                # "Yes" button in green
                if st.button("✅ Yes", type="primary"):
                    if resultados[nombre]:
                        ultimo = resultados[nombre].pop()
                        st.info(f"Last attempt for {nombre} removed ({'DNF' if ultimo[0]=='dnf' else f'{ultimo[1]:.2f}s'})")
                        rows = [{"Competidor": n, "Tipo": t, "Valor": v} for n, intentos in resultados.items() for t, v in intentos]
                        pd.DataFrame(rows).to_csv(CSV_FILE, index=False, sep=';')
                    else:
                        st.error(f"{nombre} has no attempts to delete")
                    st.session_state.confirm_undo = False
            with col_cancel_undo:
                # "No" button in red
                if st.button("❌ No"):
                    st.session_state.confirm_undo = False
        else:
            if st.button("↩️ Undo last attempt"):
                st.session_state.confirm_undo = True

    with col6:
        # Conditional buttons for Clear confirmation
        if st.session_state.confirm_clear:
            st.warning("Are you sure you want to clear all history? This action cannot be undone.")
            col_confirm_clear, col_cancel_clear = st.columns(2)
            with col_confirm_clear:
                # "Yes" button in green
                if st.button("✅ Yes", type="primary"):
                    if os.path.exists(CSV_FILE):
                        os.remove(CSV_FILE)
                    resultados = {nombre: [] for nombre in competidores.keys()}
                    st.info("History cleared. Competition reset.")
                    st.session_state.confirm_clear = False
            with col_cancel_clear:
                # "No" button in red
                if st.button("❌ No"):
                    st.session_state.confirm_clear = False
        else:
            if st.button("🗑️ Clear history"):
                st.session_state.confirm_clear = True

    # --- Logic for the new download button ---
    data_to_download = []
    for competidor, intentos in resultados.items():
        pb_inicial = competidores[competidor]
        mejor_tiempo_history = pb_inicial
        
        for i, (tipo, valor) in enumerate(intentos):
            puntos_intento = 0
            if tipo == "tiempo":
                puntos_intento = puntuar(pb_inicial, mejor_tiempo_history, valor)
                
                if valor < mejor_tiempo_history:
                    mejor_tiempo_history = valor
            
            data_to_download.append({
                "Competitor": competidor,
                "Initial PB": pb_inicial,
                "Attempt": i + 1,
                "Attempt Type": tipo,
                "Time (s)": f"{valor:.2f}" if valor else "N/A",
                "Points per Attempt": puntos_intento
            })

    df_download = pd.DataFrame(data_to_download)

    # When creating the file to download, use ';' as a separator
    csv_string = df_download.to_csv(index=False, sep=';')
    csv_buffer = io.StringIO(csv_string)

    with col7:
        st.download_button(
            label="⬇️ Download history",
            data=csv_buffer.getvalue().encode('utf-8'),
            file_name='climbing_history.csv',
            mime='text/csv',
        )

    with col8:
        if st.button("🏅 View podium"):
            st.session_state.show_podium = True
            
    def highlight_top_three_by_rank(row):
        rank = df.index.get_loc(row.name)
        styles = [''] * len(row)

        if rank == 0:
            styles = ['background-color: rgba(255, 215, 0, 0.4)'] * len(row)
        elif rank == 1:
            styles = ['background-color: rgba(192, 192, 192, 0.4)'] * len(row)
        elif rank == 2:
            styles = ['background-color: rgba(205, 127, 50, 0.4)'] * len(row)
        
        return styles

    st.subheader("📊 Live Ranking")
    st.dataframe(df.style.apply(highlight_top_three_by_rank, axis=1), use_container_width=True)

    st.subheader("📜 Attempt History")
    for nombre, intentos in resultados.items():
        historial = [f"{valor:.2f}s" if t == "tiempo" else "DNF" for t, valor in intentos]
        st.write(f"**{nombre}**: {', '.join(historial) if historial else 'No attempts'}")
        
else:
    # --- CORRECTED CODE FOR THE PODIUM ---
    st.subheader("🏆 Podium")
    st.button("↩️ Back to ranking", on_click=lambda: st.session_state.update(show_podium=False))
    
    # The index is reset so that the podium shows the names correctly
    # and those without attempts are removed
    top_3 = df[df['Attempts'] > 0].reset_index(drop=True).head(3)
    
    # Checks that there are at least 3 competitors to form a podium
    if len(top_3) >= 3:
        podium_cols = st.columns(3)

        # First place
        with podium_cols[1]:
            st.metric(label="🥇 Primer lugar", value=top_3.iloc[0]['Competitor'])
            st.caption(f"Puntos: {top_3.iloc[0]['Points']}")
            st.caption(f"Mejor tiempo: {top_3.iloc[0]['Best time']:.2f}s")
        
        # Second place
        with podium_cols[0]:
            st.metric(label="🥈 Segundo lugar", value=top_3.iloc[1]['Competitor'])
            st.caption(f"Puntos: {top_3.iloc[1]['Points']}")
            st.caption(f"Mejor tiempo: {top_3.iloc[1]['Best time']:.2f}s")

        # Third place
        with podium_cols[2]:
            st.metric(label="🥉 Tercer lugar", value=top_3.iloc[2]['Competitor'])
            st.caption(f"Puntos: {top_3.iloc[2]['Points']}")
            st.caption(f"Mejor tiempo: {top_3.iloc[2]['Best time']:.2f}s")
    else:
        st.info("Not enough competitors with attempts to form a podium.")

    # Aggiungi l'immagine del podio
    st.image("podi2.png", use_container_width=True)
