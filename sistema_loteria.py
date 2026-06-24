import streamlit as st
import pandas as pd
from pathlib import Path   # 

# ---------------- CONFIGURACIÓN GENERAL ----------------
st.set_page_config(page_title="LotoMetrika‑RD • Mapa Completo + Sistema 1220", layout="wide")
ARCHIVO = Path("data") / "raw_historical_baseline.csv"

# ---------------- 📚 CATÁLOGO OFICIAL INTEGRADO ----------------
catalogo_loterias = pd.DataFrame([
    {"nombre":"Lotería Nacional",        "tipo":"Oficial‑RD",      "horarios":"14:30;21:00;18:00‑DO", "perfil_rango":"ESTÁNDAR"},
    {"nombre":"Leidsa",                  "tipo":"Oficial‑RD",      "horarios":"20:55;15:55‑DO",        "perfil_rango":"ESTÁNDAR"},
    {"nombre":"Lotería Real",            "tipo":"Oficial‑RD",      "horarios":"12:55",                 "perfil_rango":"ESTÁNDAR"},
    {"nombre":"Loteka",                  "tipo":"Oficial‑RD",      "horarios":"19:55",                 "perfil_rango":"ESTÁNDAR"},
    {"nombre":"La Primera",              "tipo":"Oficial‑RD",      "horarios":"12:00;20:00",           "perfil_rango":"ESTÁNDAR"},
    {"nombre":"LoteDom",                 "tipo":"Oficial‑RD",      "horarios":"13:55",                 "perfil_rango":"ESTÁNDAR"},
    {"nombre":"La Suerte Dominicana",    "tipo":"Oficial‑RD",      "horarios":"12:30;18:00",           "perfil_rango":"BAJO‑PREDOMINANTE"},
    {"nombre":"King Lottery",            "tipo":"Internacional‑Caribe","horarios":"12:30;19:30",       "perfil_rango":"BAJO‑PREDOMINANTE"},
    {"nombre":"Anguila Lottery",         "tipo":"Internacional‑Caribe","horarios":"10:00;18:00;21:00",  "perfil_rango":"VARIABLE‑HORARIO"},
    {"nombre":"Florida Lottery",          "tipo":"Internacional‑Externo","horarios":"13:30;21:50",       "perfil_rango":"ESTÁNDAR‑EXTERNO"},
    {"nombre":"New York Lottery",        "tipo":"Internacional‑Externo","horarios":"14:30;22:30",       "perfil_rango":"ESTÁNDAR‑EXTERNO"}
])

# ---------------- 📂 CARGA Y LIMPIEZA DE DATOS ----------------
@st.cache_data(show_spinner="📦 Cargando base y catálogo…")
def cargar_datos():
    try:
        df = pd.read_csv(ARCHIVO, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df["turno"] = df["turno"].str.strip().str.upper()
        df["loteria"] = df["loteria"].str.strip()
        for col in ["primero","segundo","tercero"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        df = df.dropna(subset=["fecha","turno","loteria","primero","segundo","tercero"]).sort_values("fecha").reset_index(drop=True)
        # Unir con catálogo para traer perfil y tipo automáticamente
        df = df.merge(catalogo_loterias, left_on="loteria", right_on="nombre", how="left").drop(columns=["nombre"])
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar: {e}")
        return pd.DataFrame()

df_base = cargar_datos()
if df_base.empty:
    st.stop()

# ---------------- 🎛️ INTERFAZ PRINCIPAL ----------------
st.title("🗺️ LotoMetrika‑RD • Mapa Completo + Sistema 1220")

# --- RANGO DE FECHAS ---
min_fecha = df_base["fecha"].min().date()
max_fecha = df_base["fecha"].max().date()
c1,c2 = st.columns(2)
with c1: fi = st.date_input("📅 Desde", value=min_fecha, min_value=min_fecha, max_value=max_fecha)
with c2: ff = st.date_input("📅 Hasta",  value=max_fecha, min_value=min_fecha, max_value=max_fecha)

df = df_base[(df_base["fecha"]>=pd.Timestamp(fi)) & (df_base["fecha"]<=pd.Timestamp(ff))].copy()
st.info(f"✅ Período: {fi} → {ff} | Registros: {len(df)} | Último: {df['fecha'].max().date()}")

# --- FILTROS INTELIGENTES NUEVOS ---
c1,c2,c3 = st.columns(3)
with c1:
    tipos_dispon = sorted(df["tipo"].dropna().unique().tolist())
    tipo_sel = st.selectbox("🏷️ Tipo de lotería", ["TODOS"] + tipos_dispon)
with c2:
    franjas_dispon = sorted(df["turno"].unique().tolist())
    franja_sel = st.selectbox("⏱️ Franja horaria", franjas_dispon)
with c3:
    perfiles_dispon = sorted(df["perfil_rango"].dropna().unique().tolist())
    perfil_sel = st.selectbox("📘 Perfil numérico", ["TODOS"] + perfiles_dispon)

# Aplicar filtros
if tipo_sel != "TODOS": df = df[df["tipo"]==tipo_sel]
df = df[df["turno"]==franja_sel]
if perfil_sel != "TODOS": df = df[df["perfil_rango"]==perfil_sel]

if df.empty:
    st.warning("⚠️ Sin datos con estos filtros.")
    st.stop()

# --- CLASIFICACIÓN DE RANGOS ---
def rango_num(n):
    if 0<=n<=33: return "BAJO (00‑33)"
    elif 34<=n<=66: return "MEDIO (34‑66)"
    else: return "ALTO (67‑99)"

todos_nums = []
for _,f in df.iterrows():
    for pos in ["primero","segundo","tercero"]:
        todos_nums.append({
            "fecha":f["fecha"], "loteria":f["loteria"], "tipo":f["tipo"],
            "perfil":f["perfil_rango"], "numero":f[pos], "rango":rango_num(f[pos])
        })
df_n = pd.DataFrame(todos_nums)

# --- RETRASOS Y CANDIDATOS SISTEMA 1220 ---
c1,c2 = st.columns(2)
with c1: r_min = st.slider("⏳ Retraso mínimo",0,30,3)
with c2: r_max = st.slider("⏳ Retraso máximo",r_min,60,18)

ult_fecha = df["fecha"].max()
candidatos = []
for num in range(0,100):
    fechas_apar = df_n[df_n["numero"]==num]["fecha"].sort_values()
    if fechas_apar.empty: continue
    dias_retraso = (ult_fecha - fechas_apar.iloc[-1]).days
    if r_min <= dias_retraso <= r_max:
        candidatos.append({
            "Número":f"{num:02d}", "Rango":rango_num(num), "Retraso_días":dias_retraso,
            "Última vez":fechas_apar.iloc[-1].date(),
            "Derivados_1220":f"{(num+12)%100:02d}, {(num+20)%100:02d}"
        })

# --- RESULTADOS ---
st.subheader("🎯 Candidatos • Sistema 1220")
if candidatos:
    st.dataframe(pd.DataFrame(candidatos).sort_values("Retraso_días",ascending=False), use_container_width=True)
else:
    st.info("ℹ️ Sin coincidencias de retraso con estos filtros.")

# --- RESUMEN COMPARATIVO ---
with st.expander("📊 Distribución por rango y perfil"):
    st.dataframe(df_n.groupby(["perfil","rango"])["numero"].count().reset_index(name="Salidas"), use_container_width=True)
