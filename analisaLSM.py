import pandas as pd
import numpy as np
from scipy import interpolate

    # Ejemplo: Carga tabla LMS para IMC female
    df_lms = pd.read_csv('tablaIMCx.csv')  # age_days, L, M, S
    interp_L = interpolate.interp1d(df_lms['age_days'], df_lms['L'], kind='linear')
    interp_M = interpolate.interp1d(df_lms['age_days'], df_lms['M'], kind='linear')
    interp_S = interpolate.interp1d(df_lms['age_days'], df_lms['S'], kind='linear')

    def calculate_zscore(age_days, value, interp_L, interp_M, interp_S):
        L = interp_L(age_days)  # Interpola para edad exacta
        M = interp_M(age_days)
        S = interp_S(age_days)
        if L == 0:
            return np.log(value / M) / S
        else:
            return ((value / M) ** L - 1) / (L * S)

    # Prueba con tu DataFrame
    df = pd.read_csv('calculosMuestraRandom.csv', sep=';', decimal=',', encoding='latin-1')
    df['python_zscore'] = df.apply(lambda row: calculate_zscore(row['Age (d)'], row['IMCEdad_raw'], interp_L, interp_M, interp_S), axis=1)  # Ajusta para 'i'
    df['diff_python'] = df['python_zscore'] - df['IMCEdad']  # Compara con tu cálculo
    print(df[['Age (d)', 'IMCEdad', 'python_zscore', 'diff_python']])
    