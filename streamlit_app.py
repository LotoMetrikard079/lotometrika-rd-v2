import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# 📍 RUTA FIJA DENTRO DEL REPOSITORIO
CARPETA = Path(".")
ARCHIVO_DATOS = str(CARPETA / "data" / "raw_historical_baseline.csv")

# 📦 CARGA Y LIMPIEZA (IGUAL QUE TRABAJAMOS ANTES)
@st.cache_data(show_spinner="Cargando y procesando historial…")
def cargar_datos():
    df = pd.read_csv(
        ARCHIVO_DATOS,
        sep="\t",
        dtype=str,
        on_bad_lines="skip"
    )
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip())

    COLUMNAS = ["fecha","loteria","turno","primero","segundo","tercero"]
    df = df.dropna(subset=COLUMNAS)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])
    for col in ["primero","segundo","tercero"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df[(df[col]>=0)&(df[col]<=99)]
    df = df.dropna(subset=["primero","segundo","tercero"])
    return df

df = cargar_datos()

# --- 📊 LÓGICA 1220 / RETRASOS / FRANJAS — TAL CUAL LA DISEÑAMOS ---
def retraso_numero(num, df, fecha_ref=None):
    if fecha_ref is None:
        fecha_ref = datetime.today().strftime("%Y-%m-%d")
    fr = pd.to_datetime(fecha_ref)
    apar = df[(df["primero"]==num)|(df["segundo"]==num)|(df["tercero"]==num)]["fecha"]
    ant = apar[apar < fr]
    if ant.empty:
        return False, f"{num:02d}: sin salidas antes de {fecha_ref}"
    ult = ant.max()
    años = fr.year - ult.year
    meses = fr.month - ult.month
    días = fr.day - ult.day
    if días < 0:
        meses -=1; días +=31
    if meses <0:
        años -=1; meses +=12
    return True, f"{num:02d} → Últ:{ult.date()} | {años}a {meses}m {días}d"

def generar_derivados(num):
    num=int(num)
    s12=(num+12)%100
    s20=(num+20)%100
    esp=int(f"{num:02d}"[::-1])
    return [f"{num:02d}", f"{s12:02d}", f"{s20:02d}", f"{esp:02d}"]

RANGOS_TURNOS = {
    "MAÑANA": {"desde":0,"hasta":33,"etiqueta":"Bajos"},
    "TARDE": {"desde":34,"hasta":66,"etiqueta":"Medios‑Altos"},
    "NOCHE": {"desde":67,"hasta":99,"etiqueta":"Altos"}
}

def mejores_candidatos(df, turno, min_r=3, max_r=18, cant=2):
    info = RANGOS_TURNOS[turno]
    fmax = df["fecha"].max()
    largo = df.melt(id_vars=["fecha"], value_vars=["primero","segundo","tercero"], value_name="numero")
    freq = largo["numero"].value_counts()
    ult_fecha = largo.groupby("numero")["fecha"].max()
    candidatos = []
    for n in range(info["desde"], info["hasta"]+1):
        retraso_d = (fmax - ult_fecha.get(n,fmax)).days
        if min_r <= retraso_d <= max_r:
            candidatos.append((-freq.get(n,0), retraso_d, n))
    candidatos.sort()
    return [n for _,_,n in candidatos[:cant]]

# 🖥️ INTERFAZ PRÁCTICA Y LIMPIA
st.set_page_config(page_title="LotoMetrika‑RD", layout="wide")
st.title("📊 LotoMetrika‑RD — Sistema 1220 / Franjas Horarias")
st.info(f"✅ Base lista — Registros válidos: {len(df)} | Última fecha: {df['fecha'].max().date()}")

# 🎛️ CONTROLES
col1, col2, col3 = st.columns(3)
with col1:
    turno_sel = st.selectbox("Franja horaria", list(RANGOS_TURNOS.keys()), index=0)
with col2:
    min_r = st.number_input("Retraso mínimo (días)", min_value=1, max_value=60, value=3)
with col3:
    max_r = st.number_input("Retraso máximo (días)", min_value=min_r, max_value=120, value=18)

# 📈 RESULTADOS
candidatos = mejores_candidatos(df, turno_sel, min_r, max_r)
st.subheader(f"🎯 Candidatos filtrados — {turno_sel} ({RANGOS_TURNOS[turno_sel]['etiqueta']})")

for num in candidatos:
    ok, info = retraso_numero(num, df)
    deriv = generar_derivados(num)
    st.markdown(f"**{info}** | Derivados 12/Q: `{' '.join(deriv)}`")

# 📄 VER TROZO DE DATOS SI QUIERES
with st.expander("🔎 Ver muestra del historial"):
    st.dataframe(df.sort_values("fecha", ascending=False).head(20).reset_index(drop=True))
