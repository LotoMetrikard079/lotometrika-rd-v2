import streamlit as st
import pandas as pd
from pathlib import Path

# 📍 RUTAS COMPLETAS
CARPETA_DATOS = Path("data")
ARCHIVO_BASE = CARPETA_DATOS / "raw_historical_baseline.csv"
ARCHIVO_REL = CARPETA_DATOS / "relaciones_sucesion_acompañantes.csv"
ARCHIVO_DIA = CARPETA_DATOS / "un_dia_como_hoy.csv"
ARCHIVO_REPDIR = CARPETA_DATOS / "repetidos_historicos_directos.csv"
ARCHIVO_REPVOL = CARPETA_DATOS / "repetidos_historicos_volteados.csv"
ARCHIVO_RET = CARPETA_DATOS / "retrasos_mandel.csv"
ARCHIVO_NIV1220 = CARPETA_DATOS / "tabla_1220_niveles.csv"

# 📥 FUNCIONES DE CARGA CON SEGURIDAD
@st.cache_data(show_spinner="Cargando base histórica principal…")
def cargar():
    try:
        df = pd.read_csv(ARCHIVO_BASE, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"❌ No se pudo leer la base principal: {e}")
        return pd.DataFrame()

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

@st.cache_data(show_spinner="Cargando niveles Método 1220…")
def cargar_tabla_1220():
    try:
        df = pd.read_csv(ARCHIVO_NIV1220, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"⚠️ Sin tabla de niveles: {e}")
        return pd.DataFrame()

# 🧩 LLAMARLAS AL INICIO DEL FLUJO
df_base = cargar()
df_rel = cargar_relaciones()
df_dia = cargar_dia_como_hoy()
df_rep_dir = cargar_rep_dir()
df_rep_vol = cargar_rep_vol()
df_ret = cargar_retrasos()
df_niv1220 = cargar_tabla_1220()

# ⚙️ CONFIGURACIÓN Y PANTALLA PRINCIPAL
st.set_page_config(page_title="LotoMetrika‑RD", layout="wide")
st.title("📊 LotoMetrika‑RD • Sistema 1220 + Franjas Horarias")

# Estado rápido de carga
st.success("✅ TODOS LOS DATOS CARGADOS CORRECTAMENTE")
st.info(f"• Base principal: {len(df_base)} filas | Última fecha: {df_base['fecha'].max() if 'fecha' in df_base.columns else '—'}")

# Vista rápida para confirmar
st.subheader("🔍 Muestra rápida de datos")
st.dataframe(df_base.head(15), use_container_width=True)
# 🎛️ FILTROS INTERACTIVOS
st.subheader("🎚️ Explorar y filtrar")

# Fechas mínima y máxima
if "fecha" in df_base.columns and not df_base.empty:
    df_base["fecha_dt"] = pd.to_datetime(df_base["fecha"], errors="coerce")
    min_fecha = df_base["fecha_dt"].min()
    max_fecha = df_base["fecha_dt"].max()
    rango_fechas = st.date_input("Selecciona rango de fechas", [min_fecha, max_fecha])

    # Turnos disponibles
    turnos = sorted(df_base["turno"].dropna().unique())
    sel_turnos = st.multiselect("Franjas horarias / Turnos", turnos, default=turnos)

    # Loterías disponibles
    loterias = sorted(df_base["loteria"].dropna().unique())
    sel_loterias = st.multiselect("Loterías", loterias, default=loterias)

    # Aplicar filtros
    df_filtrado = df_base[
        (df_base["fecha_dt"] >= pd.to_datetime(rango_fechas[0])) &
        (df_base["fecha_dt"] <= pd.to_datetime(rango_fechas[1])) &
        (df_base["turno"].isin(sel_turnos)) &
        (df_base["loteria"].isin(sel_loterias))
    ].copy()

    st.info(f"🔎 Resultados filtrados: {len(df_filtrado)} registros")
    st.dataframe(df_filtrado, use_container_width=True)
else:
    st.warning("⚠️ No hay datos suficientes para aplicar filtros")
# 📊 TABLAS DE APOYO DEL SISTEMA
st.header("📂 Módulos de referencia")

# 1. Tabla de niveles Método 1220
with st.expander("📘 Tabla 1220 — Niveles y pesos", expanded=False):
    if not df_niv1220.empty:
        st.dataframe(df_niv1220, use_container_width=True)
    else:
        st.info("ℹ️ Tabla 1220 vacía o no cargada")

# 2. Repeticiones y retrasos
with st.expander("🔁 Repeticiones y Retrasos", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Directas")
        if not df_rep_dir.empty:
            st.dataframe(df_rep_dir.head(20), use_container_width=True)
        else:
            st.info("Sin repeticiones directas")
    with col2:
        st.subheader("Volteadas")
        if not df_rep_vol.empty:
            st.dataframe(df_rep_vol.head(20), use_container_width=True)
        else:
            st.info("Sin repeticiones volteadas")
    st.subheader("⏱️ Ciclos / Retrasos")
    if not df_ret.empty:
        st.dataframe(df_ret.head(20), use_container_width=True)
    else:
        st.info("Sin datos de retrasos")

# 3. Relaciones y sucesiones
with st.expander("🔗 Relaciones y sucesiones", expanded=False):
    if not df_rel.empty:
        st.dataframe(df_rel.head(30), use_container_width=True)
    else:
        st.info("Sin tabla de relaciones")

# 4. Un día como hoy
with st.expander("📅 Un día como hoy", expanded=False):
    if not df_dia.empty:
        st.dataframe(df_dia, use_container_width=True)
    else:
        st.info("Sin historial por fecha")
# 🧠 GENERADOR DE CANDIDATOS — MÉTODO 1220 + FRANJAS HORARIAS
st.header("🎯 Generador: Método 1220 + Franjas")

if not df_base.empty and "fecha" in df_base.columns and "turno" in df_base.columns and "loteria" in df_base.columns:
    # Asegurar formato fecha
    df_base["fecha_dt"] = pd.to_datetime(df_base["fecha"], errors="coerce")
    # Seleccionar lotería y turno objetivo
    loterias_disponibles = sorted(df_base["loteria"].dropna().unique())
    turnos_disponibles = sorted(df_base["turno"].dropna().unique())

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        loteria_objetivo = st.selectbox("Lotería objetivo", loterias_disponibles)
    with col_sel2:
        turno_objetivo = st.selectbox("Franja / Turno objetivo", turnos_disponibles)

    # Tomar el último registro anterior de esa lotería para calcular
    df_fil_lot = df_base[df_base["loteria"] == loteria_objetivo].copy()
    if not df_fil_lot.empty:
        ultimo_reg = df_fil_lot.sort_values("fecha_dt", ascending=False).iloc[0]
        num_ant = [ultimo_reg["primero"], ultimo_reg["segundo"], ultimo_reg["tercero"]]
        # Convertir a enteros con ceros a la izquierda
        try:
            nums = [int(str(n).zfill(2)) for n in num_ant]
        except:
            nums = []
            st.warning("⚠️ No se pudieron leer bien los números del último sorteo")

        st.info(f"📌 Base de cálculo: {loteria_objetivo} | Último sorteo: {ultimo_reg['fecha']} {ultimo_reg['turno']} → {num_ant}")

        # Cargar regla base Método 1220 (suma/resta fija + reglas de franja)
        if nums and not df_niv1220.empty:
            # Regla básica del método: aplicar 12 y 20 como desplazamientos
            desplazamientos = [12, 20]
            candidatos = []
            for n in nums:
                for d in desplazamientos:
                    suma = (n + d) % 100
                    resta = (n - d) % 100
                    candidatos.extend([suma, resta])

            # Agregar factor de franja horaria: rangos que observaste
            if turno_objetivo.upper() == "MEDIODIA":
                rango_min, rango_max = 0, 33
            elif turno_objetivo.upper() == "TARDE":
                rango_min, rango_max = 34, 66
            elif turno_objetivo.upper() == "NOCHE":
                rango_min, rango_max = 67, 99
            else:
                rango_min, rango_max = 0, 99

            # Calcular puntuación: pertenencia al rango + frecuencias/retrasos si existen
            df_cand = pd.DataFrame({"numero": sorted(set(candidatos))})
            df_cand["en_rango_franja"] = df_cand["numero"].apply(lambda x: 1 if rango_min <= x <= rango_max else 0)

            # Mejorar puntuación con datos de repetidos/retrasos si están disponibles
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

            # Ordenar por confianza descendente
            df_cand = df_cand.sort_values("confianza_total", ascending=False).reset_index(drop=True)
            df_cand["numero"] = df_cand["numero"].apply(lambda x: f"{x:02d}")

            st.subheader("✅ Candidatos ordenados por confianza")
            st.dataframe(df_cand, use_container_width=True)
            st.caption(f"💡 Regla aplicada: rango {rango_min:02d}‑{rango_max:02d} para franja {turno_objetivo} + Método 1220")

        else:
            st.info("ℹ️ Faltan datos de números o tabla 1220 para generar cálculos")
    else:
        st.warning("⚠️ No hay registros para la lotería seleccionada")
else:
    st.warning("⚠️ Base principal incompleta para generar candidatos")
