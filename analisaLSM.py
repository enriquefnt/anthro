import pandas as pd
import numpy as np
from scipy import interpolate
import warnings
warnings.filterwarnings('ignore')

# Imprime columnas para depuración
print("Columnas en calculosMuestraRandom.csv antes de procesamiento:")
df_data = pd.read_csv('calculosMuestraRandom.csv', sep=';', decimal=',', encoding='latin-1')
print(df_data.columns)

# Renombrar columnas para estandarizar
df_data = df_data.rename(columns={
    'Age (d)': 'Age (d)',
    'Weight (kg)': 'Weight (kg)',
    'Height (cm)': 'Height (cm)',
    'Sex': 'Sex',
})

# Convertir columnas numéricas explícitamente
numeric_cols = ['Age (d)', 'Weight (kg)', 'Height (cm)', 'IMCEdad', 'WAZ', 'HAZ', 'BAZ', 'PesoEdad', 'TallaEdad', 'difPE', 'difTE', 'difIMCE']
for col in numeric_cols:
    if col in df_data.columns:
        df_data[col] = pd.to_numeric(df_data[col], errors='coerce')

print("Tipos de datos después de conversión:")
print(df_data.dtypes)

# Función para calcular z-score
def calculate_zscore(age_days, value, L_func, M_func, S_func):
    if age_days < 0 or value <= 0 or np.isnan(value):
        return np.nan
    L = L_func(age_days)
    M = M_func(age_days)
    S = S_func(age_days)
    if L == 0:
        return np.log(value / M) / S
    else:
        return ((value / M) ** L - 1) / (L * S)

# Cargar tablaIMCx.csv
def load_lms_tables(file_path):
    df_lms = pd.read_csv(file_path)
    interp_lo = interpolate.interp1d(df_lms['age'], df_lms['lo'], kind='linear', bounds_error=False, fill_value=np.nan)
    interp_mo = interpolate.interp1d(df_lms['age'], df_lms['mo'], kind='linear', bounds_error=False, fill_value=np.nan)
    interp_so = interpolate.interp1d(df_lms['age'], df_lms['so'], kind='linear', bounds_error=False, fill_value=np.nan)
    interp_la = interpolate.interp1d(df_lms['age'], df_lms['la'], kind='linear', bounds_error=False, fill_value=np.nan)
    interp_ma = interpolate.interp1d(df_lms['age'], df_lms['ma'], kind='linear', bounds_error=False, fill_value=np.nan)
    interp_sa = interpolate.interp1d(df_lms['age'], df_lms['sa'], kind='linear', bounds_error=False, fill_value=np.nan)
    return {
        'male': (interp_lo, interp_mo, interp_so),
        'female': (interp_la, interp_ma, interp_sa)
    }

lms_tables = load_lms_tables('tablaIMCx.csv')

# Calcular IMC
df_data['IMC_calculado'] = df_data.apply(lambda row: (float(row['Weight (kg)']) / (float(row['Height (cm)']) / 100) ** 2) if pd.notna(row['Weight (kg)']) and pd.notna(row['Height (cm)']) else np.nan, axis=1)

# Función para calcular z-score
def apply_zscore(row):
    if row['Sex'] == 'Female':
        interp_L, interp_M, interp_S = lms_tables['female']
        return calculate_zscore(row['Age (d)'], row['IMC_calculado'], interp_L, interp_M, interp_S)
    elif row['Sex'] == 'Male':
        interp_L, interp_M, interp_S = lms_tables['male']
        return calculate_zscore(row['Age (d)'], row['IMC_calculado'], interp_L, interp_M, interp_S)
    else:
        return np.nan

# Aplicar el cálculo
df_data['python_IMCEdad'] = df_data.apply(apply_zscore, axis=1)

# Mostrar el dataframe
print(df_data[['Age (d)', 'Sex', 'Weight (kg)', 'Height (cm)', 'IMC_calculado', 'IMCEdad', 'python_IMCEdad', 'difIMCE']])

# Calcular diferencias
df_data['diff_python'] = df_data['python_IMCEdad'] - df_data['IMCEdad']
print("\nDiferencias con el nuevo cálculo en Python:")
print(df_data[['Age (d)', 'Sex', 'IMCEdad', 'python_IMCEdad', 'diff_python', 'difIMCE']])

# Exportar a Excel
df_data.to_excel('calculosMuestraRandom_con_zscores.xlsx', index=False, engine='openpyxl')
print("Resultados exportados a 'calculosMuestraRandom_con_zscores.xlsx'")
