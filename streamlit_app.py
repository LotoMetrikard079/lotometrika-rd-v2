import streamlit as st
import pandas as pd
from pathlib import Path

# 📍 Rutas seguras
CARPETA_DATOS = Path(__file__).resolve().parent / "data"
ARCHIVO_BASE = CARPETA_DATOS / "raw_historical_baseline.csv"
ARCHIVO_NIV1220 = CARPETA_DATOS / "tabla_1220_niveles.csv"

# 📥 Carga de datos
@st.cache_data(show_spinner="Cargando base histórica...")
def cargar_base():
    try:
        df = pd.read_csv(ARCHIVO_BASE, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        for col in ["primero","segundo","tercero"]:
            df[col] = df[col].str.zfill(2)
        return df.dropna(subset=["fecha_dt"])
    except Exception as e:
        st.error(f"Error base: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Cargando Tabla 1220...")
def cargar_tabla_1220():
    try:
        df = pd.read_csv(ARCHIVO_NIV1220, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        st.info("ℹ️ Tabla 1220 vacía o no encontrada — se usará valores por defecto")
        return pd.DataFrame({"codigo":["12","20"], "valor":["12","20"]})

# 📊 Cálculo de frecuencia y retraso
def calcular_metricas(df_filtrado):
    if df_filtrado.empty:
        return pd.DataFrame()
    nums = pd.concat([
        df_filtrado["primero"],
        df_filtrado["segundo"],
        df_filtrado["tercero"]
    ]).value_counts().reset_index()
    nums.columns = ["numero","frecuencia"]
    nums["retraso"] = 0
    fecha_max = df_filtrado["fecha_dt"].max()
    for idx, fila in nums.iterrows():
        ult = df_filtrado[
            (df_filtrado["primero"]==fila["numero"]) |
            (df_filtrado["segundo"]==fila["numero"]) |
            (df_filtrado["tercero"]==fila["numero"])
        ]["fecha_dt"].max()
        nums.at[idx, "retraso"] = (fecha_max - ult).days if pd.notna(ult) else 999
    return nums

# 🚀 Interfaz principal
st.title("🎯 LotoMetrika-RD | Sistema 1220 + Franjas Horarias")

df_base = cargar_base()
df_niv1220 = cargar_tabla_1220()

if not df_base.empty:
    min_f = df_base["fecha_dt"].min()
    max_f = df_base["fecha_dt"].max()
    rango = st.date_input("Selecciona rango de fechas", [min_f, max_f])
    loterias = sorted(df_base["loteria"].dropna().unique())
    lot_sel = st.selectbox("Lotería objetivo", loterias)
    turnos = sorted(df_base["turno"].dropna().unique())
    turno_sel = st.selectbox("Franja horaria / Turno", turnos)

    df_filt = df_base[
        (df_base["fecha_dt"] >= pd.to_datetime(rango[0])) &
        (df_base["fecha_dt"] <= pd.to_datetime(rango[1])) &
        (df_base["loteria"] == lot_sel) &
        (df_base["turno"] == turno_sel)
    ].copy()

    st.success(f"✅ Registros válidos: {len(df_filt)} | Último: {df_filt['fecha_dt'].max().strftime('%Y-%m-%d')}")

    # Regla de franja
    if turno_sel.upper() == "MAÑANA":
        rango_min, rango_max = 0, 33
    elif turno_sel.upper() == "MEDIODIA":
        rango_min, rango_max = 20, 66
    elif turno_sel.upper() == "TARDE":
        rango_min, rango_max = 40, 80
    elif turno_sel.upper() == "NOCHE":
        rango_min, rango_max = 50, 99
    else:
        rango_min, rango_max = 0, 99

    st.info(f"📌 Regla aplicada: rango {rango_min:02d}-{rango_max:02d} para franja {turno_sel}")

    # Obtener códigos 12 y 20
    cod12 = int(df_niv1220.loc[df_niv1220["codigo"]=="12","valor"].iloc[0]) if not df_niv1220.empty else 12
    cod20 = int(df_niv1220.loc[df_niv1220["codigo"]=="20","valor"].iloc[0]) if not df_niv1220.empty else 20

    metricas = calcular_metricas(df_filt)
    if not metricas.empty:
        nums_base = metricas["numero"].astype(int).tolist()
        candidatos = []
        for n in nums_base:
            for d in [cod12, cod20]:
                suma = (n + d) % 100
                resta = (n - d) % 100
                for num in [suma, resta]:
                    en_rango = 1 if rango_min <= num <= rango_max else 0
                    fila_m = metricas[metricas["numero"] == f"{num:02d}"]
                    freq = int(fila_m["frecuencia"].iloc[0]) if not fila_m.empty else 0
                    ret = int(fila_m["retraso"].iloc[0]) if not fila_m.empty else 999
                    peso = round((freq / 10) + (1 / (1 + ret / 100)), 2)
                    confianza = round(en_rango * 10 + peso, 2)
                    candidatos.append({
                        "numero": f"{num:02d}",
                        "en_rango_franja": en_rango,
                        "peso_adicional": peso,
                        "confianza_total": confianza
                    })

        df_cand = pd.DataFrame(candidatos).drop_duplicates("numero")
        df_cand = df_cand.sort_values("confianza_total", ascending=False).reset_index(drop=True)

        st.subheader("✅ Candidatos ordenados por confianza")
        st.dataframe(df_cand, use_container_width=True)

else:
    st.warning("⚠️ No se pudo cargar la base de datos")
