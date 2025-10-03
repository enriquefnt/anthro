import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# Cargar los datos desde el archivo CSV real
df = pd.read_csv('calculosMuestraRandom.csv', sep=';', decimal=',', encoding='latin-1')

# Verificar que se leyó correctamente
print("=== PRIMERAS FILAS DEL DATAFRAME ===")
print(df.head())
print("\nColumnas:", df.columns.tolist())

# Limpiar y convertir columnas numéricas
numerical_cols = ['Age (d)', 'Weight (kg)', 'Height (cm)', 'WAZ', 'HAZ', 'BAZ', 'PesoEdad', 'TallaEdad', 'IMCEdad', 
                  'DiasEdad', 'difPE', 'difTE', 'difIMCE', 'Edad años']
for col in numerical_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        print(f"Columna '{col}' convertida: dtype={df[col].dtype}, NaNs={df[col].isna().sum()}")

# Codificar 'Sex'
df['Sex_encoded'] = df['Sex'].map({'Female': 0, 'Male': 1})

# Columnas relevantes (base sin dropna global)
relevant_cols = ['Age (d)', 'Weight (kg)', 'Height (cm)', 'Sex_encoded', 'WAZ', 'HAZ', 'BAZ', 
                 'PesoEdad', 'TallaEdad', 'IMCEdad', 'difPE', 'difTE', 'difIMCE']
df_base = df[relevant_cols].copy()  # Base con todos los datos, NaN incluidos donde corresponda

# Opcional: Filtrar por edad máxima para ciertas columnas (descomenta si quieres excluir >10 años para peso/edad)
# df_base = df_base[df_base['Age (d)'] <= 3650]  # Solo hasta 10 años; ajusta según OMS

print(f"\nFilas totales en df_base: {len(df_base)}")

# Sub-DataFrames específicos para resúmenes (solo filas con datos completos en grupos clave)
df_pe = df_base[df_base['difPE'].notna()]  # Para Peso/Edad
df_te = df_base[df_base['difTE'].notna()]  # Para Talla/Edad
df_imce = df_base[df_base['difIMCE'].notna()]  # Para IMC/Edad

print("\n=== RESUMEN DE DATOS (subgrupos) ===")
print("Peso/Edad (filas con difPE no-NaN):", len(df_pe))
print(df_pe.describe())
print("\nTalla/Edad (filas con difTE no-NaN):", len(df_te))
print(df_te.describe())
print("\nIMC/Edad (filas con difIMCE no-NaN):", len(df_imce))
print(df_imce.describe())

print("\n=== MATRIZ DE CORRELACIONES GENERAL (Pearson, pairwise NaN) ===")
corr_matrix = df_base.corr(method='pearson', min_periods=2)
print(corr_matrix.round(3))

# Correlaciones específicas con diferencias
print("\n=== CORRELACIONES ESPECÍFICAS CON DIFERENCIAS (p-valor incluido) ===")
variables_to_correlate = ['Age (d)', 'Weight (kg)', 'Height (cm)', 'Sex_encoded', 'BAZ', 'IMCEdad', 'HAZ', 'TallaEdad', 'WAZ', 'PesoEdad']

for diff_col in ['difPE', 'difTE', 'difIMCE']:
    print(f"\n--- Correlaciones para {diff_col} (solo filas donde {diff_col} no es NaN) ---")
    sub_df = df_base[df_base[diff_col].notna()]
    print(f"Filas usadas: {len(sub_df)}")
    
    for var in variables_to_correlate:
        if var in sub_df.columns:
            pair_df = sub_df[[diff_col, var]].dropna()
            if len(pair_df) >= 2:
                try:
                    corr_coef, p_value = pearsonr(pair_df[diff_col], pair_df[var])
                    print(f"{diff_col} vs {var}: r = {corr_coef:.3f}, p-valor = {p_value:.3f} (n={len(pair_df)})")
                except (ImportError, NameError):
                    corr_coef = pair_df[diff_col].corr(pair_df[var])
                    print(f"{diff_col} vs {var}: r = {corr_coef:.3f} (sin p-valor, fallback usado, n={len(pair_df)})")
            else:
                print(f"{diff_col} vs {var}: No hay suficientes datos (n={len(pair_df)} < 2)")

# Análisis por sexo (ejemplo para IMC/Edad)
print("\n=== CORRELACIONES POR SEXO (ejemplo para IMC/Edad) ===")
for sex in ['Female', 'Male']:
    sex_code = 0 if sex == 'Female' else 1
    df_sex_imc = df_base[(df_base['Sex_encoded'] == sex_code) & df_base['difIMCE'].notna()][relevant_cols]
    if len(df_sex_imc) > 1:
        corr_sex = df_sex_imc.corr(method='pearson', min_periods=2)
        print(f"\nMatriz para {sex} (IMC/Edad):")
        print(corr_sex.round(3))
    else:
        print(f"\nNo hay suficientes datos para {sex} en IMC/Edad.")

# NUEVOS PLOTS: Correlaciones de Edad, Peso y Altura con cada diferencia
print("\n=== GENERANDO GRÁFICOS DE CORRELACIONES (Edad, Peso, Altura vs Diferencias) ===")

# Función auxiliar para generar plots (reutilizable)
def plot_correlations(sub_df, diff_col, title_suffix, filename):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes = axes.ravel()
    
    # Variables clave: Edad, Peso, Altura
    plots_data = [
        (sub_df['Age (d)'], sub_df[diff_col], 'Edad (días)'),
        (sub_df['Weight (kg)'], sub_df[diff_col], 'Peso (kg)'),
        (sub_df['Height (cm)'], sub_df[diff_col], 'Altura (cm)')
    ]
    
    for i, (x, y, label) in enumerate(plots_data):
        mask = ~(np.isnan(x) | np.isnan(y))  # Excluir NaN en x o y
        n_points = np.sum(mask)
        
        if n_points >= 2:
            axes[i].scatter(x[mask], y[mask], alpha=0.7, color='blue')
            axes[i].set_xlabel(label)
            axes[i].set_ylabel(diff_col)
            axes[i].set_title(f'{label} vs {diff_col} (n={n_points})')
            
            # Línea de tendencia
            z = np.polyfit(x[mask], y[mask], 1)
            p = np.poly1d(z)
            axes[i].plot(x[mask], p(x[mask]), "r--", alpha=0.8, linewidth=2)
        else:
            axes[i].text(0.5, 0.5, f'No hay datos\n(n={n_points})', ha='center', va='center', transform=axes[i].transAxes)
            axes[i].set_xlabel(label)
            axes[i].set_ylabel(diff_col)
            axes[i].set_title(f'{label} vs {diff_col}')
    
    plt.suptitle(f'Correlaciones con {title_suffix}', fontsize=16)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()

# Generar plots para cada diferencia
plot_correlations(df_pe, 'difPE', 'Diferencia Peso/Edad', 'correlaciones_difPE.png')
plot_correlations(df_te, 'difTE', 'Diferencia Talla/Edad', 'correlaciones_difTE.png')
plot_correlations(df_imce, 'difIMCE', 'Diferencia IMC/Edad', 'correlaciones_difIMCE.png')

# Histogramas (mantenido igual)
plt.figure(figsize=(10, 4))
plt.subplot(1, 3, 1)
plt.hist(df_pe['difPE'].dropna(), bins=10, alpha=0.7, edgecolor='black')
plt.xlabel('difPE')
plt.ylabel('Frecuencia')
plt.title('Errores en Peso/Edad')

plt.subplot(1, 3, 2)
plt.hist(df_te['difTE'].dropna(), bins=10, alpha=0.7, edgecolor='black')
plt.xlabel('difTE')
plt.ylabel('Frecuencia')
plt.title('Errores en Talla/Edad')

plt.subplot(1, 3, 3)
plt.hist(df_imce['difIMCE'].dropna(), bins=10, alpha=0.7, edgecolor='black')
plt.xlabel('difIMCE')
plt.ylabel('Frecuencia')
plt.title('Errores en IMC/Edad')

plt.tight_layout()
plt.savefig('distribucion_errores.png', dpi=300, bbox_inches='tight')
plt.show()

# Estadísticas de errores (por subgrupo)
print("\n=== ESTADÍSTICAS DE ERRORES (por subgrupo) ===")
for diff, sub_df in [('difPE', df_pe), ('difTE', df_te), ('difIMCE', df_imce)]:
    diffs = sub_df[diff].dropna()
    if len(diffs) > 0:
        mean_err = diffs.mean()
        std_err = diffs.std()
        rmse = np.sqrt((diffs**2).mean())
        print(f"{diff}: Media = {mean_err:.3f}, Desv. Est. = {std_err:.3f}, RMSE = {rmse:.3f} (n={len(diffs)})")
        print(f"  Rango: [{diffs.min():.3f}, {diffs.max():.3f}]")
    else:
        print(f"{diff}: No hay datos válidos.")
