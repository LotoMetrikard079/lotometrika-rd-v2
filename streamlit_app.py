# 📍 RUTAS COMPLETAS
CARPETA_DATOS = Path("data")
ARCHIVO_BASE = CARPETA_DATOS / "raw_historical_baseline.csv"
ARCHIVO_REL = CARPETA_DATOS / "relaciones_sucesion_acompañantes.csv"
ARCHIVO_DIA = CARPETA_DATOS / "un_dia_como_hoy.csv"
ARCHIVO_REPDIR = CARPETA_DATOS / "repetidos_historicos_directos.csv"
ARCHIVO_REPVOL = CARPETA_DATOS / "repetidos_historicos_volteados.csv"
ARCHIVO_RET = CARPETA_DATOS / "retrasos_mandel.csv"

# 📥 FUNCIONES DE CARGA CON SEGURIDAD
@st.cache_data(show_spinner="Cargando relaciones…")
def cargar_relaciones():
    try:
        df = pd.read_csv(ARCHIVO_REL, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"⚠️ Sin relaciones: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Cargando historia por fecha…")
def cargar_dia_como_hoy():
    try:
        df = pd.read_csv(ARCHIVO_DIA, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"⚠️ Sin datos de fecha: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Cargando repeticiones directas…")
def cargar_rep_dir():
    try:
        df = pd.read_csv(ARCHIVO_REPDIR, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"⚠️ Sin repeticiones directas: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Cargando repeticiones volteadas…")
def cargar_rep_vol():
    try:
        df = pd.read_csv(ARCHIVO_REPVOL, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"⚠️ Sin repeticiones volteadas: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Cargando ciclos y retrasos…")
def cargar_retrasos():
    try:
        df = pd.read_csv(ARCHIVO_RET, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"⚠️ Sin retrasos: {e}")
        return pd.DataFrame()

# 🧩 LLAMARLAS AL INICIO DEL FLUJO
df_base = cargar()
df_rel = cargar_relaciones()
df_dia = cargar_dia_como_hoy()
df_rep_dir = cargar_rep_dir()
df_rep_vol = cargar_rep_vol()
df_ret = cargar_retrasos()
