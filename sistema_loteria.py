import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# RUTA FIJA
ARCHIVO = Path("data") / "raw_historical_baseline.csv"

@st.cache_data(show_spinner="Cargando datos…")
def cargar():
    try:
        df = pd.read_csv(ARCHIVO, dtype=str)
        # Normalizar nombres: quitar espacios, pasar a minúsculas
        df.columns = df.columns.str.strip().str.lower()
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        return pd.DataFrame()

    # Verificar columna obligatoria
    if "fecha" not in df.columns:
        st.error("❌ Falta columna 'fecha' — revisa encabezado y separador en el CSV")
        return pd.DataFrame()

    # Convertir fecha
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    # Columnas de números
    cols_num = ["primero", "segundo", "tercero"]
    for c in cols_num:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=cols_num, how="all")

df = cargar()

# Interfaz
st.set_page_config(page_title="LotoMetrika‑RD", layout="wide")
st.title("📊 LotoMetrika‑RD • Sistema 1220 + Franjas")

if df.empty:
    st.warning("⚠️ Sin datos válidos. Revisa `data/raw_historical_baseline.csv` y su encabezado: fecha,turno,loteria,primero,segundo,tercero")
else:
    st.info(f"✅ Datos listos | Registros: {len(df)} | Último: {df['fecha'].max().date()}")

    # Rangos por franja
    RANGOS = {
        "MAÑANA": (0,33),
        "TARDE": (34,66),
        "NOCHE": (67,99)
    }
    franja = st.selectbox("Selecciona franja horaria", list(RANGOS.keys()))
    min_r = st.slider("Retraso mínimo (días)", 1, 60, 3)
    max_r = st.slider("Retraso máximo (días)", min_r, 120, 18)

    # Calcular retrasos y derivados
    if not df.empty and franja in RANGOS:
        desde,hasta = RANGOS[franja]
        ultima = df["fecha"].max()
        cols_num = ["primero","segundo","tercero"]
        largo = df.melt(id_vars=["fecha","turno"], value_vars=cols_num, var_name="pos", value_name="numero")
        largo["numero"] = pd.to_numeric(largo["numero"], errors="coerce").dropna()
        filtrado = largo[(largo["numero"]>=desde)&(largo["numero"]<=hasta)]
        ult_salida = filtrado.groupby("numero")["fecha"].max()
        retrasos = (ultima - ult_salida).dt.days
        candidatos = [n for n in retrasos.index if min_r <= retrasos[n] <= max_r]
        st.subheader(f"Candidatos — {franja} ({desde:02d}‑{hasta:02d})")
        for n in sorted(candidatos):
            der = [f"{n:02d}", f"{(n+12)%100:02d}", f"{(n+20)%100:02d}", int(f"{n:02d}"[::-1])]
            st.markdown(f"**{n:02d}** | Retraso: {retrasos[n]} días | Derivados 12/20: `{' '.join(map(str,der))}`")
