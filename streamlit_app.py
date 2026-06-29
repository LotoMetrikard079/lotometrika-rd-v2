import streamlit as st
import pandas as pd
import os

# 📍 RUTAS SEGURAS
CARPETA_DATOS = "./data"
ARCHIVO_BASE = os.path.join(CARPETA_DATOS, "raw_historical_baseline.csv")
ARCHIVO_NIV1220 = os.path.join(CARPETA_DATOS, "tabla_1220_niveles.csv")
ARCHIVO_REPDIR = os.path.join(CARPETA_DATOS, "repetidos_historicos_directos.csv")
ARCHIVO_RET = os.path.join(CARPETA_DATOS, "retrasos_mandel.csv")
ARCHIVO_RESIDUOS = os.path.join(CARPETA_DATOS, "residuos_diarios.csv")  # ✅ NUEVO

# 📥 FUNCIÓN DE CARGA
def cargar(archivo):
    try:
        if not os.path.exists(archivo):
            return pd.DataFrame()
        df = pd.read_csv(archivo, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        return pd.DataFrame()

# 📦 CARGAR TODO
df_base = cargar(ARCHIVO_BASE)
df_niv1220 = cargar(ARCHIVO_NIV1220)
df_rep_dir = cargar(ARCHIVO_REPDIR)
df_ret = cargar(ARCHIVO_RET)
df_residuos = cargar(ARCHIVO_RESIDUOS)  # ✅ CARGA RESIDUOS

# 🎨 INTERFAZ
st.set_page_config(page_title="LotoMetrika‑RD‑v2", layout="wide")
st.title("🧪 LotoMetrika‑RD‑v2")

if df_base.empty:
    st.error("⚠️ Base de datos vacía. Revisa el archivo CSV.")
    st.stop()

# Preparar fechas
df_base["fecha_dt"] = pd.to_datetime(df_base["fecha"], errors="coerce")
min_fecha = df_base["fecha_dt"].min()
max_fecha = df_base["fecha_dt"].max()

rango_fechas = st.date_input("Rango de fechas", [min_fecha.date(), max_fecha.date()])
loterias = sorted(df_base["loteria"].dropna().unique())
sel_loteria = st.selectbox("Lotería", loterias)
turnos = sorted(df_base["turno"].dropna().unique())
sel_turno = st.selectbox("Turno", turnos)

# Filtrar
filtro = (
    (df_base["fecha_dt"] >= pd.to_datetime(rango_fechas[0])) &
    (df_base["fecha_dt"] <= pd.to_datetime(rango_fechas[1])) &
    (df_base["loteria"] == sel_loteria) &
    (df_base["turno"] == sel_turno)
)
df_filtrado = df_base.loc[filtro].copy()

st.info(f"✅ Registros: {len(df_filtrado)} | Último: {df_base['fecha_dt'].max().date()}")

# Últimos números
nums = []
if not df_filtrado.empty:
    ultima = df_filtrado.sort_values("fecha_dt").iloc[-1]
    nums = [int(ultima["primero"]), int(ultima["segundo"]), int(ultima["tercero"])]
    st.write("🔢 Últimos números:", nums)

# 🧠 LÓGICA MÉTODO 1220 + AJUSTE POR RESIDUO ✅
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

    # Rango por turno
    tu = sel_turno.upper()
    if tu in ["MANANA", "MEDIODIA"]:
        rango_min, rango_max = 0, 33
    elif tu == "TARDE":
        rango_min, rango_max = 34, 66
    elif tu == "NOCHE":
        rango_min, rango_max = 67, 99
    else:
        rango_min, rango_max = 0, 99

    df_cand = pd.DataFrame({"numero": sorted(set(candidatos))})
    df_cand["en_rango"] = df_cand["numero"].apply(lambda x: 1 if rango_min <= x <= rango_max else 0)

    # Peso base
    def peso_base(n):
        n_str = f"{n:02d}"
        p = 0
        if not df_rep_dir.empty and "numero" in df_rep_dir.columns:
            fila = df_rep_dir[df_rep_dir["numero"] == n_str]
            if not fila.empty:
                p += float(fila.iloc[0].get("frecuencia", 0)) / 10
        if not df_ret.empty and "numero" in df_ret.columns:
            fila = df_ret[df_ret["numero"] == n_str]
            if not fila.empty:
                p += 1 / (1 + float(fila_r.iloc[0].get("retraso", 100)))
        return round(p, 2)

    df_cand["peso_base"] = df_cand["numero"].apply(peso_base)

    # ✅ AJUSTE POR RESIDUO INTERNO
    ajuste_residuo = 0
    if not df_residuos.empty:
        fecha_ultima = ultima["fecha"]
        fila_res = df_residuos[df_residuos["fecha"] == fecha_ultima]
        if not fila_res.empty:
            residuo = float(fila_res.iloc[0]["residuo_promedio"])
            if residuo < 45:
                ajuste_residuo = 0.15  # +15% a números altos
                df_cand.loc[df_cand["numero"] >= 45, "peso_base"] *= (1 + ajuste_residuo)
            elif residuo > 55:
                ajuste_residuo = 0.15  # +15% a números bajos
                df_cand.loc[df_cand["numero"] <= 55, "peso_base"] *= (1 + ajuste_residuo)
            # Entre 45-55 queda neutro

    # Confianza final
    df_cand["confianza_total"] = round(df_cand["en_rango"] * 10 + df_cand["peso_base"], 2)
    df_cand["numero"] = df_cand["numero"].apply(lambda x: f"{x:02d}")
    df_cand = df_cand.sort_values("confianza_total", ascending=False).reset_index(drop=True)

    st.subheader("✅ Candidatos con ajuste por Residuo Interno")
    st.dataframe(df_cand, use_container_width=True)
else:
    st.info("ℹ️ Faltan datos de Método 1220 o números para generar candidatos")
