WITH calculos AS (
  SELECT 
    ID, 
    Nombre,
    Fecha_Nacimiento, 
    Fecha_Control, 
    Sexo, 
    Peso_Kg, 
    Talla_cm,
    -- Calcular ZSCOREs una sola vez
    ZSCORE(IF(Sexo = "Femenino", 2, 1), 'p', Peso_Kg, STR_TO_DATE(Fecha_Nacimiento, '%d/%m/%Y'), STR_TO_DATE(Fecha_Control, '%d/%m/%Y')) AS PesoEdad,
    ZSCORE(IF(Sexo = "Femenino", 2, 1), 't', Talla_cm, STR_TO_DATE(Fecha_Nacimiento, '%d/%m/%Y'), STR_TO_DATE(Fecha_Control, '%d/%m/%Y')) AS TallaEdad,
    ZSCORE(IF(Sexo = "Femenino", 2, 1), 'i', (Peso_Kg / (Talla_cm / 100) / (Talla_cm / 100)), STR_TO_DATE(Fecha_Nacimiento, '%d/%m/%Y'), STR_TO_DATE(Fecha_Control, '%d/%m/%Y')) AS IMCEdad,
    -- Calcular Edad en formato 'xA xM xD'
    CONCAT(
      FLOOR(DATEDIFF(STR_TO_DATE(Fecha_Control, '%d/%m/%Y'), STR_TO_DATE(Fecha_Nacimiento, '%d/%m/%Y')) / 365.25), 'A ',
      FLOOR((DATEDIFF(STR_TO_DATE(Fecha_Control, '%d/%m/%Y'), STR_TO_DATE(Fecha_Nacimiento, '%d/%m/%Y')) % 365.25) / 30.4375), 'M ',
      FLOOR(DATEDIFF(STR_TO_DATE(Fecha_Control, '%d/%m/%Y'), STR_TO_DATE(Fecha_Nacimiento, '%d/%m/%Y')) % 30.4375), 'D'
    ) AS Edad,
    -- Calcular días entre fechas para usar en condiciones
    DATEDIFF(STR_TO_DATE(Fecha_Control, '%d/%m/%Y'), STR_TO_DATE(Fecha_Nacimiento, '%d/%m/%Y')) AS DiasEdad
  FROM saltaped_antroreg.datos_generados
  -- WHERE DATEDIFF(STR_TO_DATE(Fecha_Control, '%d/%m/%Y'), STR_TO_DATE(Fecha_Nacimiento, '%d/%m/%Y')) > (365.25 * 2)
)

SELECT 
  ID, 
    Nombre,
    Fecha_Nacimiento, 
    Fecha_Control, 
    Nombre, 
    Sexo, 
    Peso_Kg, 
    Talla_cm,
  ROUND(PesoEdad, 1) AS PesoEdad,
  ROUND(TallaEdad, 1) AS TallaEdad,
  ROUND(IMCEdad, 1) AS IMCEdad,
  Edad,
  -- Clasificación Peso usando columnas calculadas
  CASE
    WHEN (PesoEdad > 6 OR IMCEdad > 6 OR PesoEdad < -6 OR IMCEdad < -6)
      THEN "Error"
    WHEN (IMCEdad < -3 AND DiasEdad > 730) OR PesoEdad < -3
      THEN "MBP"
    WHEN (IMCEdad > -3 AND IMCEdad <= -2 AND DiasEdad > 730) OR PesoEdad < -2
      THEN "BP"
    WHEN (IMCEdad > -2 AND IMCEdad <= -1.5 AND DiasEdad > 730) OR PesoEdad < -1.5
      THEN "RBP"
    WHEN (IMCEdad > 2 AND DiasEdad > 730) OR PesoEdad > 2
      THEN "SP"
    WHEN PesoEdad >= -1.5 AND PesoEdad < 2
      THEN "AD"
  END AS ClasificacionPeso,
  -- Clasificación Talla usando TallaEdad calculado
  CASE
    WHEN TallaEdad > 6 OR TallaEdad < -6 THEN "Error"
    WHEN TallaEdad <= -3 THEN "MBT"
    WHEN TallaEdad <= -2 AND TallaEdad > -3 THEN "BT"
    WHEN TallaEdad <= -1.5 AND TallaEdad > -2 THEN "RBT"
    WHEN TallaEdad > -1.5 AND TallaEdad > -2 THEN "AD"
    WHEN TallaEdad >= -2 THEN "AT"
  END AS ClasificacionTalla
FROM calculos
ORDER BY PesoEdad, IMCEdad;