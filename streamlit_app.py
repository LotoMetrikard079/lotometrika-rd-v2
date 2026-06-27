import streamlit as st
import pandas as pd
from pathlib import Path

# 📍 RUTAS SEGURAS Y CONSISTENTES
CARPETA_DATOS = Path(__file__).resolve().parent / "data"
ARCHIVO_BASE = CARPETA_DATOS / "raw_historical_baseline.csv"
ARCHIVO_NIV1220 = CARPETA_DATOS / "tabla_1220_niveles.csv"
ARCHIVO_REL = CARPETA_DATOS / "relaciones_sucesion_acompañantes.csv"
ARCHIVO_DIA = CARPETA_DATOS / "un_dia_como_hoy.csv"
ARCHIVO_REPDIR = CARPETA_DATOS / "repetidos_historicos_directos.csv"
ARCHIVO_REPVOL = CARPETA_DATOS / "repetidos_historicos_volteados.csv"
ARCHIVO_RET = CARPETA_DATOS / "retrasos_mandel.csv"

# 📥 FUNCIONES DE CARGA CON SEGURIDAD
@st.cache_data(show_spinner="Cargando base histórica...")
def cargar_base():
    try:
        df = pd.read_csv(ARCHIVO_BASE, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        for col in ["primero", "segundo", "tercero"]:
            df[col] = df[col].str.zfill(2)
        return df.dropna(subset=["fecha_dt"])
    except Exception as e:
        st.error(f"❌ Error cargando base: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Cargando Tabla 1220...")
def cargar_tabla_1220():
    try:
        df = pd.read_csv(ARCHIVO_NIV1220, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        st.info("ℹ️ Tabla 1220 no encontrada — usando valores por defecto (12, 20)")
        return pd.DataFrame({"codigo": ["12", "20"], "valor": ["12", "20"]})

@st.cache_data(show_spinner="Cargando tablas de referencia...")
def cargar_archivo(ruta, nombre):
    try:
        df = pd.read_csv(ruta, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        st.info(f"ℹ️ {nombre} vacío o no disponible")
        return pd.DataFrame()

# 📊 CÁLCULO DE FRECUENCIA Y RETRASO
def calcular_metricas(df_filtrado):
    if df_filtrado.empty:
        return pd.DataFrame()
    todos_numeros = pd.concat([df_filtrado["primero"], df_filtrado["segundo"], df_filtrado["tercero"]])
    frecuencia = todos_numeros.value_counts().reset_index()
    frecuencia.columns = ["numero", "frecuencia"]
    fecha_max = df_filtrado["fecha_dt"].max()
    frecuencia["retraso"] = 999
    for idx, fila in frecuencia.iterrows():
        ultima_aparicion = df_filtrado[
            (df_filtrado["primero"] == fila["numero"]) |
            (df_filtrado["segundo"] == fila["numero"]) |
            (df_filtrado["tercero"] == fila["numero"])
        ]["fecha_dt"].max()
        if pd.notna(ultima_aparicion):
            frecuencia.at[idx, "retraso"] = (fecha_max - ultima_aparicion).days
    return frecuencia

# 🚀 INTERFAZ PRINCIPAL
st.set_page_config(page_title="LotoMetrika-RD", layout="wide")
st.title("🎯 LotoMetrika-RD | Sistema 1220 + Franjas + Confianza Total")

# Cargar todos los datos
df_base = cargar_base()
df_niv1220 = cargar_tabla_1220()
df_rel = cargar_archivo(ARCHIVO_REL, "Relaciones de sucesión")
df_dia = cargar_archivo(ARCHIVO_DIA, "Un día como hoy")
df_repdir = cargar_archivo(ARCHIVO_REPDIR, "Repetidos directos")
df_repvol = cargar_archivo(ARCHIVO_REPVOL, "Repetidos volteados")
df_ret = cargar_archivo(ARCHIVO_RET, "Retrasos Mandel")

if not df_base.empty:
    # CONTROLES DE FILTRADO
    min_fecha = df_base["fecha_dt"].min().date()
    max_fecha = df_base["fecha_dt"].max().date()
    rango_fechas = st.date_input("📅 Selecciona rango de fechas", [min_fecha, max_fecha])
    
    loterias_disponibles = sorted(df_base["loteria"].dropna().unique())
    loteria_sel = st.selectbox("🎰 Lotería objetivo", loterias_disponibles)
    
    turnos_disponibles = sorted(df_base["turno"].dropna().unique())
    turno_sel = st.selectbox("⏱️ Franja horaria / Turno", turnos_disponibles)

    # APLICAR FILTROS
    df_filtrado = df_base[
        (df_base["fecha_dt"] >= pd.to_datetime(rango_fechas[0])) &
        (df_base["fecha_dt"] <= pd.to_datetime(rango_fechas[1])) &
        (df_base["loteria"] == loteria_sel) &
        (df_base["turno"] == turno_sel)
    ].copy()

    st.success(f"✅ Registros válidos: {len(df_filtrado)} | Último registro: {df_filtrado['fecha_dt'].max().strftime('%Y-%m-%d') if not df_filtrado.empty else 'Sin datos'}")

    # DEFINIR RANGOS POR FRANJA
    if turno_sel.upper() == "MAÑANA":
        rango_min, rango_max = 0, 33
        regla = "00-33 → números bajos"
    elif turno_sel.upper() == "MEDIODIA":
        rango_min, rango_max = 20, 66
        regla = "20-66 → rango medio"
    elif turno_sel.upper() == "TARDE":
        rango_min, rango_max = 40, 80
        regla = "40-80 → rango medio-alto"
    elif turno_sel.upper() == "NOCHE":
        rango_min, rango_max = 50, 99
        regla = "50-99 → números altos"
    else:
        rango_min, rango_max = 0, 99
        regla = "00-99 → sin restricción"

    st.info(f"📍 Regla aplicada: {regla} para franja {turno_sel}")

    # OBTENER VALORES DEL MÉTODO 1220
    cod12 = int(df_niv1220.loc[df_niv1220["codigo"] == "12", "valor"].iloc[0]) if not df_niv1220.empty else 12
    cod20 = int(df_niv1220.loc[df_niv1220["codigo"] == "20", "valor"].iloc[0]) if not df_niv1220.empty else 20

    # CALCULAR MÉTRICAS Y CANDIDATOS
    if not df_filtrado.empty:
        metricas = calcular_metricas(df_filtrado)
        candidatos = []
        for _, fila in metricas.iterrows():
            num_base = int(fila["numero"])
            freq = int(fila["frecuencia"])
            ret = int(fila["retraso"])
            for desplazamiento in [cod12, cod20]:
                suma = (num_base + desplazamiento) % 100
                resta = (num_base - desplazamiento) % 100
                for num in [suma, resta]:
                    en_rango = 1 if rango_min <= num <= rango_max else 0
                    peso = round((freq / 10) + (1 / (1 + ret / 100)), 2)
                    confianza = round((en_rango * 10) + peso, 2)
                    candidatos.append({
                        "numero": f"{num:02d}",
                        "en_rango_franja": en_rango,
                        "peso_adicional": peso,
                        "confianza_total": confianza
                    })

        # ORDENAR Y MOSTRAR
        df_candidatos = pd.DataFrame(candidatos).drop_duplicates("numero")
        df_candidatos = df_candidatos.sort_values("confianza_total", ascending=False).reset_index(drop=True)

        st.subheader("✅ Candidatos ordenados por confianza total")
        st.dataframe(df_candidatos, use_container_width=True, height=400)

    # 📂 MÓDULOS DE REFERENCIA
    st.divider()
    st.subheader("📊 Módulos de referencia")

    with st.expander("📘 Tabla 1220 — Valores y niveles", expanded=False):
        if not df_niv1220.empty:
            st.dataframe(df_niv1220, use_container_width=True)
        else:
            st.info("ℹ️ Archivo no cargado")

    with st.expander("🔁 Relaciones de sucesión y acompañantes", expanded=False):
        if not df_rel.empty:
            st.dataframe(df_rel, use_container_width=True)
        else:
            st.info("ℹ️ Archivo no cargado")

    with st.expander("📅 Un día como hoy — Histórico por fecha", expanded=False):
        if not df_dia.empty:
            st.dataframe(df_dia, use_container_width=True)
        else:
            st.info("ℹ️ Archivo no cargado")

    with st.expander("📈 Repeticiones y retrasos", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            if not df_repdir.empty:
                st.dataframe(df_repdir, use_container_width=True)
            else:
                st.info("ℹ️ Repetidos directos")
        with col2:
            if not df_ret.empty:
                st.dataframe(df_ret, use_container_width=True)
            else:
                st.info("ℹ️ Retrasos Mandel")

else:
    st.error("❌ No se pudo cargar la base de datos principal. Verifica el archivo CSV.")
