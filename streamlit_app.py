import streamlit as st
import pandas as pd
from datetime import datetime, date
from pathlib import Path

# ---------------- CONFIGURACIÓN FIJA ----------------
st.set_page_config(page_title="LotoMetrika‑RD • Sistema 1220 + Franjas", layout="wide")
ARCHIVO = Path("data") / "raw_historical_baseline.csv"

# ---------------- CARGA Y LIMPIEZA ----------------
@st.cache_data(show_spinner="Cargando y validando base…")
def cargar_datos():
    try:
        df = pd.read_csv(ARCHIVO, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        # Fecha como fecha real
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        # Normalizar turno/franja
        df["turno"] = df["turno"].str.strip().str.upper()
        # Convertir números a entero
        for col in ["primero","segundo","tercero"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        # Eliminar filas rotas
        df = df.dropna(subset=["fecha","turno","primero","segundo","tercero"]).sort_values("fecha").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"❌ Error al leer base: {e}")
        return pd.DataFrame()

df_base = cargar_datos()

if df_base.empty:
    st.stop()

# ---------------- INTERFAZ PRINCIPAL ----------------
st.title("📊 LotoMetrika‑RD • Sistema 1220 + Franjas Horarias")

# ==== NUEVO: CONTROL DE RANGO DE FECHAS ====
min_fecha = df_base["fecha"].min().date()
max_fecha = df_base["fecha"].max().date()

col1, col2 = st.columns(2)
with col1:
    fecha_inicio = st.date_input("📅 Fecha inicial", value=min_fecha, min_value=min_fecha, max_value=max_fecha)
with col2:
    fecha_fin    = st.date_input("📅 Fecha final",   value=max_fecha, min_value=min_fecha, max_value=max_fecha)

# Filtrar datos al período seleccionado
df = df_base[
    (df_base["fecha"] >= pd.Timestamp(fecha_inicio)) &
    (df_base["fecha"] <= pd.Timestamp(fecha_fin))
].copy()

st.info(f"✅ Período: {fecha_inicio} → {fecha_fin} | Registros válidos: {len(df)} | Último en período: {df['fecha'].max().date()}")

# ==== Selección de franja horaria ====
franjas_disponibles = sorted(df["turno"].unique().tolist())
franja_elegida = st.selectbox("⏱️ Selecciona franja horaria", franjas_disponibles, index=0)
df_franja = df[df["turno"] == franja_elegida].sort_values("fecha").reset_index(drop=True)

if df_franja.empty:
    st.warning("⚠️ Sin registros para esta franja en el período elegido.")
    st.stop()

# ==== Definir rangos numéricos como acordamos ====
def clasificar_rango(n):
    if  0 <= n <=33: return "BAJO (00‑33)"
    elif 34 <= n <=66: return "MEDIO (34‑66)"
    else: return "ALTO (67‑99)"

# Unir todos los números de la franja para análisis
todos_numeros = []
for _, fila in df_franja.iterrows():
    for pos in ["primero","segundo","tercero"]:
        todos_numeros.append( {"fecha":fila["fecha"], "numero":fila[pos], "rango":clasificar_rango(fila[pos])} )
df_nums = pd.DataFrame(todos_numeros)

# ==== Filtros de retraso ====
col_min, col_max = st.columns(2)
with col_min:
    retraso_min = st.slider("⏳ Retraso mínimo (días)", 0, 30, 3)
with col_max:
    retraso_max = st.slider("⏳ Retraso máximo (días)", retraso_min, 60, 18)

# Calcular retraso por número dentro del período
ultima_fecha_periodo = df_franja["fecha"].max()
candidatos = []

for num in range(0,100):
    apariciones = df_nums[df_nums["numero"]==num]["fecha"].sort_values()
    if apariciones.empty: continue
    ult_fecha = apariciones.iloc[-1]
    dias_retraso = (ultima_fecha_periodo - ult_fecha).days
    if retraso_min <= dias_retraso <= retraso_max:
        rango_asignado = clasificar_rango(num)
        # Aplicar lógica base del Sistema 1220: derivados simples (+12, +20 módulo 100)
        d1 = (num +12) % 100
        d2 = (num +20) % 100
        candidatos.append( {
            "Número": f"{num:02d}",
            "Rango": rango_asignado,
            "Retraso_dias": dias_retraso,
            "Última vez": ult_fecha.date(),
            "Derivados_1220": f"{d1:02d}, {d2:02d}"
        } )

# ==== RESULTADOS ====
st.subheader(f"🎯 Candidatos — {franja_elegida} • Período {fecha_inicio} → {fecha_fin}")
if candidatos:
    df_cand = pd.DataFrame(candidatos).sort_values("Retraso_dias", ascending=False).reset_index(drop=True)
    st.dataframe(df_cand, use_container_width=True)
else:
    st.info("ℹ️ Ningún número cumple los límites de retraso en este período/franja.")

# ==== RESUMEN COMPARATIVO DE RANGOS ====
with st.expander("📊 Resumen de distribución por rango en este período"):
    resumen_rango = df_nums.groupby("rango")["numero"].count().reset_index()
    resumen_rango["%"] = (100 * resumen_rango["numero"] / resumen_rango["numero"].sum()).round(1)
    resumen_rango.columns = ["Rango numérico", "Cantidad salidas", "Porcentaje (%)"]
    st.dataframe(resumen_rango, use_container_width=True)
