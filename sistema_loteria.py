import pandas as pd
import os
from datetime import datetime
from io import StringIO

import sys
from pathlib import Path

# 📍 RUTA SEGURA, NO IMPORTA DESDE DÓNDE EJECUTES
CARPETA_PROYECTO = Path(__file__).resolve().parent
ARCHIVO = str(CARPETA_PROYECTO / "data" / "raw_historical_baseline.csv")
print("🔍 Verificando ubicación...")
if not os.path.exists(ARCHIVO):
    print(f"❌ NO ENCONTRADO: {ARCHIVO} → revisa carpeta/data/nombre")
    exit()

print("📄 Leyendo y limpiando base completa...")
try:
    with open(ARCHIVO, "rb") as f:
        contenido_bruto = f.read()
    contenido_limpio = contenido_bruto.replace(b"\x00", b"").decode("utf-8", errors="ignore")
    df = pd.read_csv(
    StringIO(contenido_limpio),
    sep="\t",      # ← ESTE ES EL CAMBIO: usa TABULACIÓN, no coma
    dtype=str,
    on_bad_lines="skip"
)

# ✅ VALIDACIÓN DE ESTRUCTURA
COLUMNAS_REQUERIDAS = ["fecha","loteria","turno","primero","segundo","tercero"]
if not all(col in df.columns for col in COLUMNAS_REQUERIDAS):
    print(f"❌ FALTAN COLUMNAS OBLIGATORIAS: debe tener {COLUMNAS_REQUERIDAS}")
    exit()

# 🧹 PREPARACIÓN Y LIMPIEZA DE DATOS
df = df.dropna(subset=COLUMNAS_REQUERIDAS)
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
df = df.dropna(subset=["fecha"])
for col in ["primero","segundo","tercero"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[(df[col] >= 0) & (df[col] <= 99)]
df = df.dropna(subset=["primero","segundo","tercero"])

print(f"✅ BASE CARGADA — Registros válidos: {len(df)}")

# --- 📊 MÉTODO 1220: CÁLCULO DE RETRASO ---
def retraso_numero(num, fecha_referencia=None):
    if fecha_referencia is None:
        fecha_referencia = datetime.today().strftime("%Y-%m-%d")
    fr = pd.to_datetime(fecha_referencia)
    apariciones = df[(df["primero"]==num)|(df["segundo"]==num)|(df["tercero"]==num)]["fecha"]
    anteriores = apariciones[apariciones < fr]
    if anteriores.empty:
        return False, f"{num:02d}: sin salidas antes de {fecha_referencia}"
    ultima_salida = anteriores.max()
    años = fr.year - ultima_salida.year
    meses = fr.month - ultima_salida.month
    días = fr.day - ultima_salida.day
    if días < 0:
        meses -= 1; días += 31
    if meses < 0:
        años -= 1; meses += 12
    return True, f"{num:02d} → Últ:{ultima_salida.date()} | {años}a {meses}m {días}d"

# --- ⚙️ REGLAS OPERATIVAS 1220 + CÓDIGO Q / ESPEJO ---
def generar_derivados(num):
    num = int(num)
    suma12 = (num + 12) % 100
    suma20 = (num + 20) % 100
    espejo = int(f"{num:02d}"[::-1])
    return [f"{num:02d}", f"{suma12:02d}", f"{suma20:02d}", f"{espejo:02d}"]

# --- 🎯 SELECCIÓN POR FRANJA HORARIA / RANGO ---
RANGOS_TURNOS = {
    "MAÑANA": {"desde":0,"hasta":33,"etiqueta":"Bajos"},
    "TARDE": {"desde":34,"hasta":66,"etiqueta":"Medios‑Altos"},
    "NOCHE": {"desde":67,"hasta":99,"etiqueta":"Altos"}
}

def mejores_candidatos_por_turno(turno, lim_retraso_min=3, lim_retraso_max=18, cantidad=2):
    info = RANGOS_TURNOS[turno]
    fecha_mas_reciente = df["fecha"].max()
    tabla_expandida = df.melt(
        id_vars=["fecha"],
        value_vars=["primero","segundo","tercero"],
        value_name="numero"
    )
    frecuencia = tabla_expandida["numero"].value_counts()
    ultima_fecha_salida = tabla_expandida.groupby("numero")["fecha"].max()
    lista_candidatos = []
    for n in range(info["desde"], info["hasta"]+1):
        retraso_días = (fecha_mas_reciente - ultima_fecha_salida.get(n, fecha_mas_reciente)).days
        if lim_retraso_min <= retraso_días <= lim_retraso_max:
            lista_candidatos.append((-frecuencia.get(n,0), retraso_días, n))
    lista_candidatos.sort()
    return [n for _,_,n in lista_candidatos[:cantidad]]

# --- 🚀 EJECUCIÓN PRINCIPAL CON TU BASE COMPLETA ---
print("\n=== SISTEMA INTEGRADO: FILTRO + REGLAS 1220 / Q ===")
for nombre_turno in RANGOS_TURNOS:
    print(f"\n▶ FRANJA: {nombre_turno} | RANGO: {RANGOS_TURNOS[nombre_turno]['etiqueta']}")
    seleccionados = mejores_candidatos_por_turno(nombre_turno)
    print(f"  → CANDIDATOS FILTRADOS: {[f'{x:02d}' for x in seleccionados]}")
    for num in seleccionados:
        ok, info_retraso = retraso_numero(num)
        print(f"    • {info_retraso}")
        print(f"      → DERIVADOS 12/Q: {' '.join(generar_derivados(num))}")

print("\n✅ PROCESO FINALIZADO — Base completa cargada y analizada")
