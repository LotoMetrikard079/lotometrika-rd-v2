
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# RUTA CORRECTA DENTRO DEL REPO
CARPETA = Path(".")
ARCHIVO_DATOS = str(CARPETA / "data" / "raw_historical_baseline.csv")

@st.cache_data(show_spinner="Cargando historial de sorteos…")
def cargar_datos():
    # Leer con separador de tabulaciones y limpiar nombres de columnas
    df = pd.read_csv(
        ARCHIVO_DATOS,
        sep="\t",
        dtype=str,
        on_bad_lines="skip"
    )
    # LIMPIEZA OBLIGATORIA: quita espacios de nombres y valores
    df.columns = df.columns.str.strip().str.lower()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # NOMBRES UNIFICADOS SEGÚN TU ESTRUCTURA ORIGINAL
    columnas_esperadas = ["fecha", "loteria", "turno", "primero", "segundo", "tercero", "cuarto", "quinto"]
    # Dejar solo las que existan, sin romper
    df = df.reindex(columns=[c for c in columnas_esperadas if c in df.columns])

    # Procesar fecha y números
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["fecha"])
    for col in ["primero", "segundo", "tercero", "cuarto", "quinto"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=[col])
            df = df[(df[col] >= 0) & (df[col] <= 99)]
    return df

df = cargar_datos()

# --- LÓGICA 1220 / FRANJAS / RETRASOS ---
def retraso_numero(num, df, fecha_ref=None):
    if fecha_ref is None:
        fecha_ref = datetime.today().strftime("%Y-%m-%d")
    fr = pd.to_datetime(fecha_ref)
    cols_numeros = [c for c in ["primero", "segundo", "tercero", "cuarto", "quinto"] if c in df.columns]
    apariciones = df[df[cols_numeros].eq(num).any(axis=1)]["fecha"]
    anteriores = apariciones[apariciones < fr]
    if anteriores.empty:
        return False, f"{num:02d}: sin salidas registradas antes de {fecha_ref}"
    ultima = anteriores.max()
    años = fr.year - ultima.year
    meses = fr.month - ultima.month
    días = fr.day - ultima.day
    if días < 0:
        meses -= 1
        días += 31
    if meses < 0:
        años -= 1
        meses += 12
    return True, f"{num:02d} → Última: {ultima.date()} | Retraso: {años}a {meses}m {días}d"

def generar_derivados(num):
    num = int(num)
    s12 = (num + 12) % 100
    s20 = (num + 20) % 100
    espejo = int(f"{num:02d}"[::-1])
    return [f"{num:02d}", f"{s12:02d}", f"{s20:02d}", f"{espejo:02d}"]

RANGOS = {
    "MAÑANA": {"desde": 0, "hasta": 33, "etiqueta": "Bajos (00‑33)"},
    "TARDE": {"desde": 34, "hasta": 66, "etiqueta": "Medios‑Altos (34‑66)"},
    "NOCHE": {"desde": 67, "hasta": 99, "etiqueta": "Altos (67‑99)"}
}

def mejores_candidatos(df, franja, min_retraso=3, max_retraso=18, cantidad=2):
    info = RANGOS[franja]
    fecha_max = df["fecha"].max()
    cols_numeros = [c for c in ["primero", "segundo", "tercero", "cuarto", "quinto"] if c in df.columns]
    largo = df.melt(id_vars=["fecha"], value_vars=cols_numeros, var_name="pos", value_name="numero")
    frecuencia = largo["numero"].value_counts()
    ultima_fecha_por_num = largo.groupby("numero")["fecha"].max()
    lista = []
    for n in range(info["desde"], info["hasta"] + 1):
        if n not in ultima_fecha_por_num.index:
            continue
        dias_retraso = (fecha_max - ultima_fecha_por_num.loc[n]).days
        if min_retraso <= dias_retraso <= max_retraso:
            lista.append((‑frecuencia.get(n, 0), dias_retraso, n))
    lista.sort()
    return [n for _, _, n in lista[:cantidad]]

# 🖥️ INTERFAZ SEGURA
st.set_page_config(page_title="LotoMetrika‑RD", layout="wide")
st.title("📊 LotoMetrika‑RD • Sistema 1220 + Franjas Horarias")
st.info(f"✅ Datos listos | Registros válidos: {len(df)} | Último sorteo: {df['fecha'].max().date()}")

c1, c2, c3 = st.columns(3)
with c1: franja_sel = st.selectbox("Franja horaria", list(RANGOS.keys()), index=0)
with c2: min_d = st.number_input("Retraso mínimo (días)", min_value=1, max_value=60, value=3)
with c3: max_d = st.number_input("Retraso máximo (días)", min_value=min_d, max_value=120, value=18)

st.subheader(f"🎯 Candidatos para {franja_sel} — {RANGOS[franja_sel]['etiqueta']}")
for num in mejores_candidatos(df, franja_sel, min_d, max_d):
    ok, texto = retraso_numero(num, df)
    st.markdown(f"**{texto}** | Derivados 12/Q: `{' '.join(generar_derivados(num))}`")

with st.expander("🔎 Ver muestra del historial"):
    st.dataframe(df.sort_values("fecha", ascending=False).head(20).reset_index(drop=True))

