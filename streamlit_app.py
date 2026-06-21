import streamlit as st
import pandas as pd
from pathlib import Path

# RUTA FIJA
ARCHIVO = Path("data") / "raw_historical_baseline.csv"

st.set_page_config(page_title="LotoMetrika‑RD", layout="wide")
st.title("📊 LotoMetrika‑RD • Sistema 1220 + Franjas")

@st.cache_data(show_spinner="Leyendo archivo…")
def cargar_datos():
    try:
        # Leer tal cual primero
        df = pd.read_csv(ARCHIVO, dtype=str)
        # Mostrar columnas leídas para verificar
        st.info(f"🔍 Columnas detectadas: {list(df.columns)}")
        # LIMPIEZA FUERTE: quitar espacios, pasar a minúsculas
        df.columns = df.columns.str.strip().str.lower()
        # Verificar obligatorias
        necesarias = ["fecha", "turno", "loteria", "primero", "segundo", "tercero"]
        faltan = [c for c in necesarias if c not in df.columns]
        if faltan:
            st.error(f"❌ FALTAN COLUMNAS: {faltan} — Revisa encabezado y que el separador sea COMA")
            return pd.DataFrame()
        # Convertir tipos
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["fecha"])
        for col in ["primero", "segundo", "tercero"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception as e:
        st.error(f"💥 ERROR AL LEER: {str(e)}")
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("⚠️ SIN DATOS VÁLIDOS — Revisa el archivo CSV: debe estar en `data/raw_historical_baseline.csv` y empezar con:")
    st.code("fecha,turno,loteria,primero,segundo,tercero")
else:
    st.success(f"✅ LISTO | Registros válidos: {len(df)} | Último sorteo: {df['fecha'].max().date()}")

    # --- LÓGICA DE FRANJAS Y SISTEMA 1220 ---
    RANGOS = {"MAÑANA": (0,33), "TARDE": (34,66), "NOCHE": (67,99)}
    franja = st.selectbox("Selecciona franja horaria", list(RANGOS.keys()))
    min_r = st.slider("Retraso mínimo (días)", 1, 60, 3)
    max_r = st.slider("Retraso máximo (días)", min_r, 120, 18)

    desde,hasta = RANGOS[franja]
    ultima_fecha = df["fecha"].max()
    cols_números = ["primero", "segundo", "tercero"]

    # Poner todo en fila para calcular retrasos
    df_largo = df.melt(
        id_vars=["fecha", "turno"],
        value_vars=cols_números,
        var_name="posición",
        value_name="número"
    ).dropna(subset=["número"])
    df_largo["número"] = df_largo["número"].astype(int)

    # Filtrar por rango de la franja
    df_filtrado = df_largo[(df_largo["número"] >= desde) & (df_largo["número"] <= hasta)]
    ultima_salida = df_filtrado.groupby("número")["fecha"].max()
    retrasos = (ultima_fecha - ultima_salida).dt.days

    # Mostrar candidatos dentro del rango de retraso
    st.subheader(f"🎯 Candidatos — {franja} ({desde:02d}‑{hasta:02d})")
    encontrados = False
    for num in sorted(retrasos.index):
        r = retrasos[num]
        if min_r <= r <= max_r:
            # Derivados del Sistema 1220
            der_12 = (num + 12) % 100
            der_20 = (num + 20) % 100
            inverso = int(f"{num:02d}"[::-1])
            st.markdown(f"**{num:02d}** | Retraso: {r} días → Derivados: `{der_12:02d} {der_20:02d} {inverso:02d}`")
            encontrados = True
    if not encontrados:
        st.info("ℹ️ Ningún número cumple los filtros actuales; prueba ampliar rango o cambiar franja.")
