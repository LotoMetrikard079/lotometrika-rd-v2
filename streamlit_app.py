import streamlit as st
import pandas as pd
import os

# 📍 RUTAS SEGURAS Y COMPLETAS
CARPETA_DATOS = "./data"
ARCHIVO_BASE = os.path.join(CARPETA_DATOS, "raw_historical_baseline.csv")
ARCHIVO_NIV1220 = os.path.join(CARPETA_DATOS, "tabla_1220_niveles.csv")
ARCHIVO_REPDIR = os.path.join(CARPETA_DATOS, "repetidos_historicos_directos.csv")
ARCHIVO_REPVOL = os.path.join(CARPETA_DATOS, "repetidos_historicos_volteados.csv")  # ✅ AGREGADO
ARCHIVO_RET = os.path.join(CARPETA_DATOS, "retrasos_mandel.csv")
ARCHIVO_RESIDUOS = os.path.join(CARPETA_DATOS, "residuos_diarios.csv")

# 📥 FUNCIÓN DE CARGA ROBUSTA
def cargar(archivo):
    try:
        if not os.path.exists(archivo):
            return pd.DataFrame()
        df = pd.read_csv(archivo, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"ℹ️ No se pudo cargar {os.path.basename(archivo)}: {e}")
        return pd.DataFrame()

# 📦 CARGAR TODOS LOS ARCHIVOS
df_base = cargar(ARCHIVO_BASE)
df_niv1220 = cargar(ARCHIVO_NIV1220)
df_rep_dir = cargar(ARCHIVO_REPDIR)
df_rep_vol = cargar(ARCHIVO_REPVOL)  # ✅ CARGA VOLTEADOS
df_ret = cargar(ARCHIVO_RET)
df_residuos = cargar(ARCHIVO_RESIDUOS)

# 🎨 INTERFAZ PRINCIPAL
st.set_page_config(page_title="LotoMetrika‑RD‑v2.1", layout="wide")
st.title("🧪 LotoMetrika‑RD‑v2.1")

if df_base.empty:
    st.error("⚠️ Base de datos vacía. Revisa el archivo raw_historical_baseline.csv")
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

# Filtrar datos
filtro = (
    (df_base["fecha_dt"] >= pd.to_datetime(rango_fechas[0])) &
    (df_base["fecha_dt"] <= pd.to_datetime(rango_fechas[1])) &
    (df_base["loteria"] == sel_loteria) &
    (df_base["turno"] == sel_turno)
)
df_filtrado = df_base.loc[filtro].copy()

st.info(f"✅ Registros: {len(df_filtrado)} | Último: {df_base['fecha_dt'].max().date()}")

# 📊 INDICADOR IDI Y TENDENCIA
if not df_residuos.empty:
    df_residuos["fecha_dt"] = pd.to_datetime(df_residuos["fecha"])
    ultimo_res = df_residuos.sort_values("fecha_dt").iloc[-1]
    st.metric(
        label=f"IDI {ultimo_res['fecha']}",
        value=f"{ultimo_res['idi_certificado']}",
        delta=f"{ultimo_res['regimen']} | N={ultimo_res['n_sorteos']}"
    )
    if ultimo_res["regimen"] == "CONTRACCION":
        st.success("📈 Tendencia: **AL ALZA** → priorizar números ≥ 45")
    elif ultimo_res["regimen"] == "EXPANSION":
        st.warning("📉 Tendencia: **A LA BAJA** → priorizar números ≤ 55")
    else:
        st.info("⚖️ Tendencia: **EQUILIBRIO** → sin preferencia")

# Últimos números extraídos
nums = []
if not df_filtrado.empty:
    ultima = df_filtrado.sort_values("fecha_dt").iloc[-1]
    nums = [int(ultima["primero"]), int(ultima["segundo"]), int(ultima["tercero"])]
    st.write("🔢 Últimos números:", nums)

# 🧠 LÓGICA COMPLETA + MÉTODO 1220 + FRECUENCIAS + RETRASOS + AJUSTE RESIDUO
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

    # Rango de validez según turno
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

    # ✅ PESO BASE MEJORADO: Directos + Volteados + Retrasos
    def peso_base(n):
        n_str = f"{n:02d}"
        p = 0.0
        # Frecuencia directa
        if not df_rep_dir.empty and "numero" in df_rep_dir.columns:
            fila = df_rep_dir[df_rep_dir["numero"] == n_str]
            if not fila.empty:
                p += int(fila.iloc[0]["frecuencia"]) / 10
        # Frecuencia volteada
        if not df_rep_vol.empty and "numero" in df_rep_vol.columns:
            fila_v = df_rep_vol[df_rep_vol["numero"] == n_str]
            if not fila_v.empty:
                p += int(fila_v.iloc[0]["frecuencia"]) / 20
        # Retraso Mandel
        if not df_ret.empty and "numero" in df_ret.columns:
            fila_r = df_ret[df_ret["numero"] == n_str]
            if not fila_r.empty:
                retraso = float(fila_r.iloc[0]["retraso"])
                p += 1 / (1 + retraso)
        return round(p, 2)

    df_cand["peso_base"] = df_cand["numero"].apply(peso_base)

    # ✅ AJUSTE POR RESIDUO INTERNO
    if not df_residuos.empty:
        fecha_ultima = ultima["fecha"]
        fila_res = df_residuos[df_residuos["fecha"] == fecha_ultima]
        if not fila_res.empty:
            residuo = float(fila_res.iloc[0]["idi_certificado"])
            if residuo < 35:
                df_cand["ajuste"] = df_cand["numero"].apply(lambda x: 1.15 if x >= 45 else 1.0)
            elif residuo > 55:
                df_cand["ajuste"] = df_cand["numero"].apply(lambda x: 1.15 if x <= 55 else 1.0)
            else:
                df_cand["ajuste"] = 1.0
            df_cand["peso_base"] = round(df_cand["peso_base"] * df_cand["ajuste"], 2)
        else:
            df_cand["ajuste"] = 1.0
    else:
        df_cand["ajuste"] = 1.0

    # Cálculo final de confianza
    df_cand["confianza_total"] = round(df_cand["en_rango"] * 10 + df_cand["peso_base"], 2)
    df_cand["numero"] = df_cand["numero"].apply(lambda x: f"{x:02d}")
    df_cand = df_cand.sort_values("confianza_total", ascending=False).reset_index(drop=True)

    st.subheader("✅ Candidatos — Frecuencia 15 años + Residuo")
    st.dataframe(df_cand[["numero", "en_rango", "peso_base", "ajuste", "confianza_total"]], use_container_width=True)
else:
    st.info("ℹ️ Faltan datos del Método 1220 o números para generar candidatos")
