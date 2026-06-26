
import streamlit as st
import pandas as pd
from pathlib import Path

# 📍 RUTAS ABSOLUTAS SEGURAS — NO FALLAN
CARPETA_DATOS = Path(__file__).resolve().parent / "data"

ARCHIVO_BASE = CARPETA_DATOS / "raw_historical_baseline.csv"
ARCHIVO_REL = CARPETA_DATOS / "relaciones_sucesion_acompañantes.csv"
ARCHIVO_DIA = CARPETA_DATOS / "un_dia_como_hoy.csv"
ARCHIVO_REPDIR = CARPETA_DATOS / "repetidos_historicos_directos.csv"
ARCHIVO_REPVOL = CARPETA_DATOS / "repetidos_historicos_volteados.csv"
ARCHIVO_RET = CARPETA_DATOS / "retrasos_mandel.csv"
ARCHIVO_NIV1220 = CARPETA_DATOS / "tabla_1220_niveles.csv"


# 📥 FUNCIONES DE CARGA GENERALES
@st.cache_data(show_spinner="Cargando base principal…")
def cargar_base():
    try:
        df = pd.read_csv(ARCHIVO_BASE, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        if "fecha" in df.columns:
            df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"❌ Base principal: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Cargando tabla 1220…")
def cargar_tabla_1220():
    try:
        df = pd.read_csv(ARCHIVO_NIV1220, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"❌ Tabla 1220: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Cargando repeticiones directas…")
def cargar_rep_dir():
    try:
        df = pd.read_csv(ARCHIVO_REPDIR, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return pd.DataFrame()

@st.cache_data(show_spinner="Cargando retrasos…")
def cargar_retrasos():
    try:
        df = pd.read_csv(ARCHIVO_RET, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return pd.DataFrame()

# (puedes agregar igual el resto: relaciones, día como hoy, volteados… si los usas)


# ⚙️ EJECUTAR CARGAS AL INICIO
df_base = cargar_base()
df_niv1220 = cargar_tabla_1220()
df_rep_dir = cargar_rep_dir()
df_ret = cargar_retrasos()


# ==================================================
# 🎛️ INTERFAZ, FILTROS Y SELECCIÓN — AQUÍ SE CREAN nums y turno_objetivo
# ==================================================
st.set_page_config(page_title="LotoMetrika‑RD", layout="wide")
st.title("📊 LotoMetrika‑RD • Sistema 1220 + Franjas Horarias")

if df_base.empty:
    st.error("⚠️ No se pudo cargar la base de datos principal. Revisa el archivo CSV.")
    st.stop()

# Rango de fechas
min_fecha = df_base["fecha_dt"].min()
max_fecha = df_base["fecha_dt"].max()
rango_fechas = st.date_input("Selecciona rango de fechas", [min_fecha, max_fecha])

# Lotería y turno
loterias_disponibles = sorted(df_base["loteria"].dropna().unique())
sel_loteria = st.selectbox("Lotería objetivo", loterias_disponibles)

turnos_disponibles = sorted(df_base["turno"].dropna().unique())
turno_objetivo = st.selectbox("Franja horaria / Turno", turnos_disponibles)

# Filtrar datos según selección
filtro = (
    (df_base["fecha_dt"] >= pd.to_datetime(rango_fechas[0])) &
    (df_base["fecha_dt"] <= pd.to_datetime(rango_fechas[1])) &
    (df_base["loteria"] == sel_loteria) &
    (df_base["turno"] == turno_objetivo)
)
df_filtrado = df_base.loc[filtro].copy()

st.info(f"✅ Registros válidos: {len(df_filtrado)} | Último: {df_base['fecha_dt'].max().date()}")

# 📌 OBTENER NÚMEROS DEL ÚLTIMO SORTEO DISPONIBLE → AQUÍ SE DEFINE nums
nums = []
if not df_filtrado.empty:
    ultima_fila = df_filtrado.sort_values("fecha_dt").iloc[-1]
    nums = [
        int(ultima_fila["primero"]),
        int(ultima_fila["segundo"]),
        int(ultima_fila["tercero"])
    ]
    st.write("🔢 Números del sorteo anterior:", nums)


# ==================================================
# 🧠 LÓGICA DE CÁLCULO — YA TIENE nums y turno_objetivo ✅
# ==================================================
if nums and not df_niv1220.empty:
    cod12 = int(df_niv1220.loc[df_niv1220["codigo"] == "12", "valor"].iloc[0])
    cod20 = int(df_niv1220.loc[df_niv1220["codigo"] == "20", "valor"].iloc[0])
    desplazamientos = [cod12, cod20]

    candidatos = []
    for n in nums:
        for d in desplazamientos:
            suma = (n + d) % 100
            resta = (n - d) % 100
            candidatos.extend([suma, resta])

    # 🎯 RANGO POR FRANJA HORARIA
    tu = turno_objetivo.upper()
    if tu == "MEDIODIA":
        rango_min, rango_max = 0, 33
    elif tu == "TARDE":
        rango_min, rango_max = 34, 66
    elif tu == "NOCHE":
        rango_min, rango_max = 67, 99
    elif tu == "MAÑANA":
        rango_min, rango_max = 0, 33
    else:
        rango_min, rango_max = 0, 99

    # 📊 CALCULAR PESOS Y CONFIANZA
    df_cand = pd.DataFrame({"numero": sorted(set(candidatos))})
    df_cand["en_rango_franja"] = df_cand["numero"].apply(lambda x: 1 if rango_min <= x <= rango_max else 0)

    def obtener_peso(n):
        peso = 0
        n_str = f"{n:02d}"
        if not df_rep_dir.empty and "numero" in df_rep_dir.columns:
            fila = df_rep_dir[df_rep_dir["numero"] == n_str]
            if not fila.empty:
                peso += float(fila.iloc[0].get("frecuencia", 0)) / 10
        if not df_ret.empty and "numero" in df_ret.columns:
            fila_r = df_ret[df_ret["numero"] == n_str]
            if not fila_r.empty:
                peso += 1 / (1 + float(fila_r.iloc[0].get("retraso", 100)))
        return round(peso, 2)

    df_cand["peso_adicional"] = df_cand["numero"].apply(obtener_peso)
    df_cand["confianza_total"] = round(df_cand["en_rango_franja"] * 10 + df_cand["peso_adicional"], 2)
    df_cand = df_cand.sort_values("confianza_total", ascending=False).reset_index(drop=True)
    df_cand["numero"] = df_cand["numero"].apply(lambda x: f"{x:02d}")

    st.subheader("✅ Candidatos ordenados por confianza")
    st.dataframe(df_cand, use_container_width=True)
    st.caption(f"💡 Regla aplicada: rango {rango_min:02d}‑{rango_max:02d} para franja {turno_objetivo} + Método 1220")
else:
    st.info("ℹ️ Faltan datos de números o tabla 1220 para generar cálculos")

