
import streamlit as st
import pandas as pd
from pathlib import Path

# 📍 RUTA ABSOLUTA SEGURA — NO FALLA DONDE SE EJECUTE
CARPETA_DATOS = Path(__file__).resolve().parent / "data"
ARCHIVO_NIV1220 = CARPETA_DATOS / "tabla_1220_niveles.csv" # ✅ NOMBRE ACTUALIZADO

# 📥 CARGA DE LA TABLA 1220
@st.cache_data(show_spinner="Cargando tabla Método 1220…")
def cargar_tabla_1220():
    try:
        df = pd.read_csv(ARCHIVO_NIV1220, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"❌ No se pudo leer tabla 1220: {e}")
        return pd.DataFrame()

# ✅ EJECUTAR CARGA AL INICIO
df_niv1220 = cargar_tabla_1220()

# ==================================================
# ⚠️ AQUÍ DEBES TENER EL RESTO DE TU CÓDIGO:
# Cargas de df_base, df_rep_dir, df_ret, controles, filtros,
# selección de lotería, lectura de números anteriores → AQUÍ SE CREAN:
# nums = [...] y turno_objetivo = "MEDIODIA"/"TARDE"/"NOCHE"
# ==================================================

# 🧠 LÓGICA DE CÁLCULO — SOLO AQUÍ, DESPUÉS DE QUE EXISTAN LAS VARIABLES
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

    # 🎯 RANGO POR FRANJA HORARIA — TU REGLA
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

    # 📊 CALCULAR PESOS Y CONFIANZA — TAL COMO LO DISEÑAMOS
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


