import pandas as pd
import numpy as np
from scipy import interpolate
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Función para calcular z-score
def calculate_zscore(age_days, value, L, M, S):
    if np.isnan(age_days) or np.isnan(value) or value <= 0:
        return np.nan
    if L == 0:
        return np.log(value / M) / S
    else:
        return ((value / M) ** L - 1) / (L * S)

# Cargar y estandarizar tablas LMS
def load_lms_tables():
    tables = {}
    for table_name in ['tablaPEx', 'tablaTEx', 'tablaIMCx', 'tablaPE6x', 'tablaTE6x', 'tablaIMC6x']:
        df = pd.read_csv(table_name + '.csv')  # Asume que los archivos son e.g., tablaPEx.csv
        # Convertir columnas numéricas a numérico
        numeric_cols = [col for col in df.columns if col not in ['idIMC']]  # Asume idIMC es string, ajusta si necesario
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        tables[table_name] = df
    return tables

tables = load_lms_tables()

# Función para interpolar LMS basado en edad y sexo
def get_interpolated_lms(indicator, age_days, sexo):
    if sexo not in ['m', 'f']:
        return np.nan, np.nan, np.nan
    if age_days <= 1825:  # Diaria
        df = tables[indicator + 'x']
        if sexo == 'm':
            interp_L = interpolate.interp1d(df['age'], df['lo'], kind='linear', bounds_error=False, fill_value=np.nan)
            interp_M = interpolate.interp1d(df['age'], df['mo'], kind='linear', bounds_error=False, fill_value=np.nan)
            interp_S = interpolate.interp1d(df['age'], df['so'], kind='linear', bounds_error=False, fill_value=np.nan)
        else:
            interp_L = interpolate.interp1d(df['age'], df['la'], kind='linear', bounds_error=False, fill_value=np.nan)
            interp_M = interpolate.interp1d(df['age'], df['ma'], kind='linear', bounds_error=False, fill_value=np.nan)
            interp_S = interpolate.interp1d(df['age'], df['sa'], kind='linear', bounds_error=False, fill_value=np.nan)
        return interp_L(age_days), interp_M(age_days), interp_S(age_days)
    else:
        age_months = age_days / 30.4375
        df = tables[indicator + '6x']
        if sexo == 'm':
            interp_L = interpolate.interp1d(df['age_s'], df['lo'], kind='linear', bounds_error=False, fill_value=np.nan)
            interp_M = interpolate.interp1d(df['age_s'], df['mo'], kind='linear', bounds_error=False, fill_value=np.nan)
            interp_S = interpolate.interp1d(df['age_s'], df['so'], kind='linear', bounds_error=False, fill_value=np.nan)
        else:
            interp_L = interpolate.interp1d(df['age_s'], df['la'], kind='linear', bounds_error=False, fill_value=np.nan)
            interp_M = interpolate.interp1d(df['age_s'], df['ma'], kind='linear', bounds_error=False, fill_value=np.nan)
            interp_S = interpolate.interp1d(df['age_s'], df['sa'], kind='linear', bounds_error=False, fill_value=np.nan)
        return interp_L(age_months), interp_M(age_months), interp_S(age_months)

# Cargar el archivo de datos y estandarizar
df_data = pd.read_csv('datosAntro.csv', sep=';', decimal=',', encoding='latin-1')
numeric_cols_data = ['FechaNacimiento', 'FechaControl', 'Peso', 'Talla', 'Age (d)', 'IMCEdad']  # Ajusta según columnas
for col in numeric_cols_data:
    if col in df_data.columns and col not in ['FechaNacimiento', 'FechaControl']:  # Fechas no son numéricas
        df_data[col] = pd.to_numeric(df_data[col], errors='coerce')

# Calcular edad en días
df_data['edad_dias'] = df_data.apply(lambda row: (datetime.strptime(row['FechaControl'], '%d/%m/%Y') - datetime.strptime(row['FechaNacimiento'], '%d/%m/%Y')).days, axis=1)

# Calcular IMC
df_data['IMC_calculado'] = df_data.apply(lambda row: (float(row['Peso']) / (float(row['Talla']) / 100) ** 2) if pd.notna(row['Peso']) and pd.notna(row['Talla']) else np.nan, axis=1)

# Calcular z-scores
def calculate_all_zscores(row):
    sexo = row['Sexo'].lower()  # 'm' or 'f'
    age_days = row['edad_dias']
    
    if age_days <= 3650:  # Peso/Edad hasta 10 años
        L, M, S = get_interpolated_lms('tablaPE', age_days, sexo)
        row['PesoEdad_Z'] = calculate_zscore(age_days, row['Peso'], L, M, S)
    else:
        row['PesoEdad_Z'] = np.nan
    
    if age_days <= 6935:  # Talla/Edad hasta 19 años
        L, M, S = get_interpolated_lms('tablaTE', age_days, sexo)
        row['TallaEdad_Z'] = calculate_zscore(age_days, row['Talla'], L, M, S)
    else:
        row['TallaEdad_Z'] = np.nan
    
    if age_days <= 6935:  # IMC/Edad hasta 19 años
        L, M, S = get_interpolated_lms('tablaIMC', age_days, sexo)
        row['IMCEdad_Z'] = calculate_zscore(age_days, row['IMC_calculado'], L, M, S)
    else:
        row['IMCEdad_Z'] = np.nan
    
    return row

df_data = df_data.apply(calculate_all_zscores, axis=1)

# Mostrar resultados
print(df_data[['FechaNacimiento', 'FechaControl', 'Sexo', 'Peso', 'Talla', 'IMC_calculado', 'PesoEdad_Z', 'TallaEdad_Z', 'IMCEdad_Z']])

# Exportar a Excel
df_data.to_excel('z_scores_resultados.xlsx', index=False, engine='openpyxl')
print("Resultados exportados a 'z_scores_resultados.xlsx'")
