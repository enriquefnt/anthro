import random
import string
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import csv
import math

# Función para generar un ID único de 7 caracteres alfanuméricos
def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

# Listas de nombres aleatorios en español
NOMBRES_MASCULINOS = [
    'Juan', 'Carlos', 'Miguel', 'José', 'Antonio', 'Francisco', 'Manuel', 'David', 'Javier', 'Daniel',
    'Pedro', 'Luis', 'Diego', 'Alejandro', 'Fernando', 'Raúl', 'Sergio', 'Pablo', 'Angel', 'Roberto',
    'Enrique','Gustavo','Mario','Kevin','Leonardo', 'Esteban','Roque','Jonathan','Armando','Joel',
    'Hector'
]
NOMBRES_FEMENINOS = [
    'María', 'Ana', 'Carmen', 'Laura', 'Sofía', 'Isabel', 'Pilar', 'Cristina', 'Elena', 
    'Marta', 'Sara', 'Paula', 'Clara', 'Beatriz', 'Rosa', 'Teresa', 'Julia', 'Nuria', 'Alba',
    'Rosa','Gabriela','Estela','Yesica','Angeles','Margarita','Estela','Luisa','Patricia','Estela',
    'Fernanda'

]

def generar_nombre(sexo):
    if sexo.lower() == 'm':
        return random.choice(NOMBRES_MASCULINOS)
    else:
        return random.choice(NOMBRES_FEMENINOS)

# Fecha de referencia: 30/09/2025
fecha_referencia = datetime(2025, 9, 30)
FECHA_CONTROL_STR = "30/09/2025"

# Rango de fechas de nacimiento: 1 día a 18 años al 30/09/2025
# 18 años atrás: 30/09/2007 (exacto: 6570 días aprox.)
fecha_inicio = fecha_referencia - timedelta(days=365.25 * 18)  # Aprox. 6574 días
fecha_fin = fecha_referencia - timedelta(days=1)  # 29/09/2025

def random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

# Cargar la tabla de estándares
try:
    df = pd.read_csv('estandares.csv', sep=',')  # Ajusta sep si es ';' o tab
    # Limpiar: convertir Rotulo a string si hay NULLs
    df['Rotulo'] = df['Rotulo'].fillna('')  # Ignoramos Rotulo
    df['edadDias'] = pd.to_numeric(df['edadDias'], errors='coerce')
    print("Tabla cargada exitosamente. Filas:", len(df))
except FileNotFoundError:
    print("Error: Crea 'estandares.csv' con tu tabla completa.")
    exit(1)

# Columnas mapeadas por tipo y sexo
COLUMNAS_PESO = {
    'f': ['SD3negPEF', 'SD2negPEF', 'SD1negPEF', 'SD0PEF', 'SD1PEF', 'SD2PEF', 'SD3PEF'],
    'm': ['SD3negPEM', 'SD2negPEM', 'SD1negPEM', 'SD0PEM', 'SD1PEM', 'SD2PEM', 'SD3PEM']
}
ZS_PESO = [-3, -2, -1, 0, 1, 2, 3]  # z-scores correspondientes

COLUMNAS_TALLA = {
    'f': ['SD3negTEF', 'SD2negTEF', 'SD1negTEF', 'SD0TEF', 'SD1TEF', 'SD2TEF', 'SD3TEF'],
    'm': ['SD3negTEM', 'SD2negTEM', 'SD1negTEM', 'SD0TEM', 'SD1TEM', 'SD2TEM', 'SD3TEM']
}

COLUMNAS_IMC = {
    'f': ['SD3negIEF', 'SD2negIEF', 'SD1negIEF', 'SD0IEF', 'SD1IEF', 'SD2IEF', 'SD3IEF'],
    'm': ['SD3negIEM', 'SD2negIEM', 'SD1negIEM', 'SD0IEM', 'SD1IEM', 'SD2IEM', 'SD3IEM']
}

# Función para calcular edad en días
def calcular_edad_dias(fecha_nac, fecha_ref):
    delta = fecha_ref - fecha_nac
    return delta.days

# Función para interpolar valor en una fila para un z dado
def interpolar_valor(z, columnas, zs, row):
    if z <= -3:
        # Extrapolar abajo
        idx = 0
        val1 = row[columnas[0]]
        val2 = row[columnas[1]]
        dist = abs(z - zs[0])
        return max(0.1, val1 - (val2 - val1) * dist)  # Clamp mínimo para evitar negativos
    elif z >= 3:
        # Extrapolar arriba
        idx = len(zs) - 1
        val1 = row[columnas[-1]]
        val2 = row[columnas[-2]]
        dist = z - zs[-1]
        return val1 + (val1 - val2) * dist
    else:
        # Interpolar lineal
        idx = np.searchsorted(zs, z)
        z1, z2 = zs[idx-1], zs[idx]
        val1, val2 = row[columnas[idx-1]], row[columnas[idx]]
        frac = (z - z1) / (z2 - z1)
        return val1 + frac * (val2 - val1)

# Función para buscar/interpolar en tabla por edadDias
def buscar_fila_edad(edad_dias, df):
    # Encontrar filas cercanas
    idx = np.argmin(np.abs(df['edadDias'] - edad_dias))
    row = df.iloc[idx]
    # Si no exacta, interpolar entre dos filas (simple: usa la más cercana por ahora; ajusta si necesitas precisión)
    if abs(df.iloc[idx]['edadDias'] - edad_dias) > 1:
        prev_idx = max(0, idx - 1)
        next_idx = min(len(df) - 1, idx + 1)
        if prev_idx != idx and next_idx != idx:
            prev_row = df.iloc[prev_idx]
            next_row = df.iloc[next_idx]
            weight = (edad_dias - prev_row['edadDias']) / (next_row['edadDias'] - prev_row['edadDias'])
            # Interpolar solo las columnas numéricas relevantes (simplificado)
            for col in COLUMNAS_PESO['m'] + COLUMNAS_TALLA['m'] + COLUMNAS_IMC['m']:  # Cubre todas
                if col in row.index:
                    row[col] = prev_row[col] + weight * (next_row[col] - prev_row[col])
    return row

# Función para calcular talla
def calcular_talla(edad_dias, sexo, z_talla, df):
    row = buscar_fila_edad(edad_dias, df)
    columnas = COLUMNAS_TALLA[sexo]
    valor = interpolar_valor(z_talla, columnas, ZS_PESO, row)  # ZS_PESO sirve para talla también
    return round(valor, 1)

# Función para calcular peso
def calcular_peso(edad_dias, sexo, z_peso, z_imc, df, talla=None):
    EDAD_MAX_PESO = 3650  # 10 años aprox.
    if edad_dias <= EDAD_MAX_PESO:
        # Usar Peso/Edad
        row = buscar_fila_edad(edad_dias, df)
        columnas = COLUMNAS_PESO[sexo]
        valor = interpolar_valor(z_peso, columnas, ZS_PESO, row)
        return round(valor, 1)
    else:
        # Usar IMC/Edad + talla
        row = buscar_fila_edad(edad_dias, df)
        columnas_imc = COLUMNAS_IMC[sexo]
        imc = interpolar_valor(z_imc, columnas_imc, ZS_PESO, row)
        talla_m = talla / 100
        peso = imc * (talla_m ** 2)
        return round(peso, 1)

# Generar 150 datos
datos = []
while len(datos) < 300:
    fecha_nac = random_date(fecha_inicio, fecha_fin)
    edad_dias = calcular_edad_dias(fecha_nac, fecha_referencia)
    if edad_dias < 1 or edad_dias > (365.25 * 18):
        continue  # Asegura rango
    
    fecha_str = fecha_nac.strftime('%d/%m/%Y')  # Formato DD/MM/AAAA
    id_unico = generate_id()
    sexo = random.choice(['m', 'f'])
    nombre = generar_nombre(sexo)
    
    z_talla = round(random.uniform(-4, 4), 1)
    talla = calcular_talla(edad_dias, sexo, z_talla, df)
    
    if edad_dias <= 3650:
        z_peso = round(random.uniform(-4, 4), 1)
        peso = calcular_peso(edad_dias, sexo, z_peso, None, df)
        z_imc = None  # No usado
    else:
        z_imc = round(random.uniform(-4, 4), 1)
        peso = calcular_peso(edad_dias, sexo, None, z_imc, df, talla)
    
    datos.append([id_unico, nombre, fecha_str, FECHA_CONTROL_STR, peso, talla, sexo.upper()])

# Imprimir en formato CSV separado por ";"
print("ID;Nombre;Fecha_Nacimiento;Fecha_Control;Peso_Kg;Talla_cm;Sexo")
for fila in datos:
    print(';'.join(map(str, fila)))

# Guardar a archivo
with open('datos_generados.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(["ID", "Nombre", "Fecha_Nacimiento", "Fecha_Control", "Peso_Kg", "Talla_cm", "Sexo"])
    writer.writerows(datos)
print("\nDatos guardados en 'datos_generados.csv' (150 filas)")

