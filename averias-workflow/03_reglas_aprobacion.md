# 03 — Reglas de aprobación por umbral de costo

## Principios

1. **El umbral se mide en `CostoTotalUSD` bruto** (cantidad × costo Infor ÷ tipo de cambio), no en la pérdida neta. El valor recuperable lo estima quien quiere que le aprueben, así que usarlo para bajar de tramo invita a la manipulación.
2. **Todas las averías pasan por N1**, incluso las de $5. No hay autoaprobación. Las averías son un canal clásico para tapar faltantes o robo, y el costo de N1 es de unos 3 minutos por caso. El control de fondo de las averías pequeñas lo hace Power BI (concentración por reportante, tienda y SKU), no más niveles de aprobación.
3. **Los niveles son acumulativos y secuenciales:** un caso T3 pasa por N1 → valorización → N2 → N3. No se hacen en paralelo, porque el N2 operativo es quien corrige la causa y el responsable antes de que lo vea el N3.
4. **Anti-fraccionamiento:** el tramo se calcula sobre el **mayor** de dos valores, el costo del caso o el acumulado del mismo SKU en la misma ubicación durante los últimos `VentanaFraccionamientoDias` (7) días, contando casos no rechazados ni anulados. Si el acumulado sube el tramo, se marca `AlertaFraccionamiento = Sí` y el aprobador lo ve en el correo de aprobación.
5. **Segregación:** nadie aprueba su propio reporte ni aprueba dos niveles del mismo caso. Si el aprobador resuelto coincide con el reportante o con un aprobador anterior, el flujo pasa al suplente; si el suplente también choca, pasa al nivel siguiente.
6. **La regla se congela al enrutar:** `VersionRegla`, `Tramo`, `NivelesRequeridos` y `FechaLimiteCierre` se escriben una vez. Cambiar los parámetros afecta solo a los casos nuevos.

## Parámetros editables (sin tocar los flujos)

Todos viven en listas de SharePoint; editarlos no requiere TI ni cambiar los flujos.

| Lista | Qué se edita | Ejemplo |
|---|---|---|
| `Cfg_Umbrales` | Rangos USD, niveles requeridos, roles por nivel, SLA por nivel, SLA de cierre y vigencia | Fila `*` (regional) y, si un país necesita otra cosa, una fila con su `PaisCodigo` que la reemplaza |
| `Cfg_Parametros` | Ventana anti-fraccionamiento, horas de recordatorio y escalamiento, SLA de valorización y de ajuste Infor, umbral acumulado mensual por tienda | `VentanaFraccionamientoDias = 7` |
| `Cfg_Aprobadores` | Quién es cada rol por país y ubicación, con su suplente | El jefe de tienda SV-T014 y su suplente |
| `Cfg_TipoCambio` | Tipo de cambio mensual por moneda | `2026-12, GTQ, 7.70` |

**Resolución de la regla:** el flujo busca en `Cfg_Umbrales` las filas `Activo = Sí` vigentes a la fecha de envío para `PaisCodigo = país del caso`. Si no hay ninguna, usa `PaisCodigo = *`. Dentro del conjunto toma la fila donde `MontoDesdeUSD <= monto <= MontoHastaUSD`.

**Resolución del aprobador:** en `Cfg_Aprobadores`, con `Rol = RolNx` y `Activo = Sí`, busca primero `PaisCodigo = país` y `UbicacionCodigo = código exacto`, después `PaisCodigo = país` y `UbicacionCodigo = *`, y por último `PaisCodigo = *` (lo usa el rol regional).

**Cambios de versión:** para cambiar los umbrales no se editan las filas vigentes. Se pone `VigenteHasta` en las actuales y se cargan filas nuevas con otra `Version` (p. ej. `B-2027.1`) y `VigenteDesde`. Así Power BI puede comparar el desempeño antes y después.

## Escenarios de umbral

La decisión de costo tiene incertidumbre: hoy no conocemos la distribución real de las averías por monto. Abajo hay tres juegos de umbrales evaluados con dos volúmenes. **Las cifras de entrada son supuestos para dimensionar, no datos de Unicomer**; con 2 o 3 meses de casos reales en la lista se recalibran (ver "Recalibración").

### Supuestos

- Volumen bajo: 2 averías por tienda al mes × 600 tiendas + 40 por CD al mes × 6 CD = **1 440 averías/mes**.
- Volumen alto: 4 por tienda + 60 por CD = **2 760 averías/mes**.
- Distribución por monto (USD): <50: 50 % · 50–100: 15 % · 100–250: 15 % · 250–500: 8 % · 500–1 000: 5 % · 1 000–2 500: 3.5 % · 2 500–5 000: 2 % · 5 000–10 000: 1 % · >10 000: 0.5 %. Costo promedio ≈ $385 por caso.
- Tiempo de aprobación por caso: N1 3 min · N2 5 min · N3 8 min · N4 10 min.
- N4 es la gerencia de logística regional (una persona para los 6 países); N3 es la gerencia de logística de cada país.

### Umbrales por escenario (desde dónde entra cada nivel, USD)

| Escenario | N1 | N2 | N3 | N4 |
|---|---|---|---|---|
| A — Control | todo | ≥ 100 | ≥ 500 | ≥ 2 500 |
| **B — Base (recomendado)** | todo | **≥ 250** | **≥ 1 000** | **≥ 5 000** |
| C — Ágil | todo | ≥ 500 | ≥ 2 500 | ≥ 10 000 |

### Resultado con volumen bajo (1 440/mes)

| Escenario | Casos N2/mes | Casos N3/mes | Casos N4/mes | N3 por país por día hábil | N4 por día hábil | % del costo revisado por ≥N2 | % del costo revisado por ≥N3 | Horas de aprobación/mes (todos los niveles) |
|---|---|---|---|---|---|---|---|---|
| A — Control | 504 | 173 | 50 | 1.3 | 2.3 | 95 % | 81 % | 145 |
| **B — Base** | **288** | **101** | **22** | **0.8** | **1.0** | **88 %** | **72 %** | **113** |
| C — Ágil | 173 | 50 | 7 | 0.4 | 0.3 | 81 % | 57 % | 94 |

### Resultado con volumen alto (2 760/mes)

| Escenario | Casos N2/mes | Casos N3/mes | Casos N4/mes | N3 por país por día hábil | N4 por día hábil | % del costo revisado por ≥N2 | % del costo revisado por ≥N3 | Horas de aprobación/mes |
|---|---|---|---|---|---|---|---|---|
| A — Control | 966 | 331 | 97 | 2.5 | 4.4 | 95 % | 81 % | 279 |
| **B — Base** | **552** | **193** | **41** | **1.5** | **1.9** | **88 %** | **72 %** | **217** |
| C — Ágil | 331 | 97 | 14 | 0.7 | 0.6 | 81 % | 57 % | 181 |

### Lectura y recomendación

Recomiendo arrancar con **B — Base**. El argumento central es que la distribución de averías está muy concentrada: un 20 % de los casos (≥ $250) concentra cerca del 88 % del costo. B pone la revisión gerencial (N2) justo donde está el dinero y deja que el 80 % de los casos se resuelva con N1 más la valorización.

- **A — Control** sube la cobertura de N2 del 88 % al 95 % del costo, pero casi duplica los casos N2 (de 288 a 504 al mes) y le manda entre 2 y 4 casos diarios a N4. A ese volumen la aprobación regional se vuelve un sello sin revisión real y se convierte en el cuello de botella del SLA. Ese 7 % adicional de costo se controla mejor con analítica que con firmas.
- **C — Ágil** reduce las horas de aprobación apenas un 17 % frente a B, pero deja sin revisión de N3 el 43 % del costo. El ahorro de tiempo es chico frente al hueco de control.
- **El riesgo de B** está en el tramo $100–$250 (15 % de los casos, ~6 % del costo), que solo ve N1. Lo cubren el anti-fraccionamiento, el umbral acumulado mensual por ubicación (`UmbralAcumuladoTiendaMesUSD = 3 000`, que avisa a N3) y el indicador de concentración por reportante en Power BI.
- **Sensibilidad al volumen:** si el volumen real se parece al alto, B sigue siendo manejable para N3 (1.5 casos por país por día). La alerta es N4: con más de 2 casos diarios hay que subir N4 a ≥ $10 000 y dejar el resto de B igual.

### Señales para recalibrar (revisar al mes 3)

| Señal en Power BI | Acción |
|---|---|
| N4 recibe más de 2 casos por día hábil durante 4 semanas | Subir N4 a $10 000 |
| Mediana de aprobación de N2 o N3 > 24 h | Revisar primero los aprobadores (suplentes, carga); si el problema es estructural, subir el umbral de ese nivel un escalón |
| Casos en $200–$249 por encima de 1.5 veces los de $250–$299 (amontonamiento bajo el umbral) | Señal de fraccionamiento o de cantidades ajustadas: auditar esas ubicaciones y bajar N2 a $200 en el país afectado |
| % de rechazo en N2 o N3 < 2 % sostenido | Ese nivel no está agregando control; evaluar subir su umbral |
| % de rechazo en N1 > 10 % en una ubicación | Problema de capacitación del reportante, no de umbral |

### Recalibración con datos reales

Con 3 meses de casos valorizados, en Power BI se arma el histograma de `CostoTotalUSD` con los mismos cortes de la tabla de supuestos. Se reemplaza la distribución supuesta por la real y se recalculan los casos y horas por escenario: casos de Nx = casos con costo ≥ umbral de Nx; horas = Σ casos de cada nivel × minutos del nivel ÷ 60. La medida `[Simulacion casos N2]` del archivo DAX lo hace con un parámetro "qué pasaría si".

## SLA

| Tramo | Rango USD | Niveles | SLA de aprobación por nivel | SLA de cierre (desde el envío) |
|---|---|---|---|---|
| T1 | 0 – 249.99 | N1 | 24 h | 7 días |
| T2 | 250 – 999.99 | N1, N2 | 24 h | 10 días |
| T3 | 1 000 – 4 999.99 | N1, N2, N3 | 24 h | 15 días |
| T4 | ≥ 5 000 | N1 a N4 | 24 h | 20 días |

Además: la valorización tiene un SLA de 24 h y el ajuste en Infor, de 3 días desde la aprobación final.

- **Cierre** = aprobado + ajuste registrado en Infor (`NumeroAjusteInfor`) + evidencia de la disposición ejecutada (acta de destrucción, guía de RTV, N.º de reclamo o factura outlet). **El cobro del reclamo no forma parte del cierre:** un proveedor puede tardar meses en pagar, y meterlo en el cierre ensucia el SLA operativo. La recuperación se mide aparte con `MontoRecuperadoUSD`.
- Los SLA corren en **horas calendario**, no hábiles. Calcular horas hábiles con feriados de 6 países en Power Automate es frágil y caro en acciones; 24 h calendario con escalamiento a las 48 h es un compromiso razonable. Si los fines de semana distorsionan el indicador, Power BI puede reportar además una versión en días hábiles usando la tabla de fechas.
