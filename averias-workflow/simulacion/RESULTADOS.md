# Simulacro de la regla de recurrencia (D2)

**Pregunta:** ¿la regla de recurrencia propuesta detecta los problemas reales sin saturar a Control de Inventarios (CI)?

**Respuesta corta:** **la regla original (V1) no pasa la prueba.** Detecta todo, pero manda a CI el **49 % de los casos** (5.7 por día hábil por país), porque los SKUs, proveedores y tiendas grandes caen en "recurrencia" solo por volumen. La versión ajustada que recomiendo (**V3 con R3b = 3 000**) baja la carga a **1.7 casos por día hábil**, detecta las 5 tiendas problema, los 3 SKUs defectuosos y el proveedor malo, y reduce a 0.9 por mes los SKUs normales marcados.

## Cómo se armó

`simulacro_recurrencia.py` genera un país sintético. Son 240 días de historia previa más **360 días evaluados**, en **30 corridas** con semillas distintas (se reportan promedios).

| Elemento | Supuesto |
|---|---|
| Volumen | 100 tiendas × ~2 casos/mes + CD con 40 casos/mes ≈ **259 casos/mes** |
| Tamaño de tienda | Lognormal (σ = 0.45, media 1). Las tiendas grandes tienen más averías **legítimas** |
| SKUs y proveedores | 3 000 SKUs con popularidad Zipf (el top concentra ~3 % de las averías); 80 proveedores, unos pocos grandes |
| Responsable | Tienda: 40 % tienda, 25 % proveedor, 20 % transporte, 10 % entrega, 5 % otro. CD: 45 % CD, 40 % proveedor, 15 % transporte |
| Costo | Unitario lognormal (mediana USD 150, σ = 1.0); 80 % de los casos con 1 unidad, 15 % con 2–5, 5 % con 6–20 |

**Anomalías plantadas** (lo que la regla debería encontrar):

| Anomalía | Cuántas | Comportamiento | Desde |
|---|---|---|---|
| Tienda problema | 5 | 2.5 veces más averías, 70 % imputadas a la tienda | Día 90 de la evaluación |
| Tienda "cara" | 2 | Frecuencia normal, pero averías 3 veces más caras (patrón típico para tapar faltantes) | Día 90 |
| SKU defectuoso | 3 | +5 casos/mes, 80 % imputables al proveedor, durante 120 días | Día 120 |
| Proveedor malo | 1 | +6 casos/mes imputables, en varios SKUs, durante 150 días | Día 150 |

## Variantes probadas

| Variante | R1 (SKU) | R2 (proveedor) | R3a (tienda, frecuencia) | R3b (tienda, monto) |
|---|---|---|---|---|
| **V0 Literal** | ≥ 2 casos/60 d | ≥ 2 casos/60 d | ≥ 2 casos/60 d | — |
| **V1 Propuesta** (la que te pasé) | ≥ 3 casos/60 d, todos los responsables | ≥ 5 imputables/60 d | ≥ 6 casos/30 d, igual para todas las tiendas | ≥ USD 3 000/30 d |
| **V2 Ajustada** | Solo imputables al proveedor; umbral = máx(3, k de la **tasa propia del SKU**) | Umbral = máx(5, k de la **tasa propia del proveedor**) | k según el **tamaño de la tienda**, α = 2.5 % | ≥ USD 3 000 × tamaño |
| **V3** | Igual que V2 | Igual que V2 | k por tamaño, **α = 1 %** | **≥ 3 casos** y ≥ USD X × tamaño (X = 3 000, 5 000 o sin R3b) |

*Tasa propia* significa los casos del mismo SKU o proveedor entre 240 y 60 días atrás, llevados a 60 días. La regla salta cuando el SKU o el proveedor se aparta de **su propio nivel normal**.

## Resultados (por país, promedio de 30 corridas)

| Métrica | V0 Literal | V1 Propuesta | V2 Ajustada | **V3 R3b=3000** | V3 R3b=5000 | V3 sin R3b |
|---|---|---|---|---|---|---|
| **% de casos a CI por recurrencia** | 88.3 | 48.6 | 17.5 | **14.3** | 11.0 | 8.8 |
| **Casos a CI por día hábil** | 10.4 | 5.7 | 2.1 | **1.7** | 1.3 | 1.0 |
| R1 casos/mes | 95.4 | 53.6 | 4.5 | 4.5 | 4.5 | 4.5 |
| R2 casos/mes | 63.2 | 46.6 | 9.4 | 9.4 | 9.4 | 9.4 |
| R3a casos/mes | 188.8 | 36.9 | 19.2 | 11.9 | 11.9 | 11.9 |
| R3b casos/mes | 0 | 34.3 | 22.1 | 19.2 | 7.9 | 0 |
| **Tiendas problema detectadas (de 5)** | 5.0 | 4.9 | 5.0 | **5.0** | 5.0 | 5.0 |
| Días para detectar una tienda problema | 9 | 44 | 41 | 49 | 56 | 63 |
| **Tiendas caras detectadas (de 2)** | 2.0 | 1.9 | 1.9 | **1.6** | 1.2 | 0.4 |
| Días para detectar una tienda cara | 29 | 59 | 62 | 62 | 79 | 149 |
| Tiendas normales marcadas al menos una vez en 12 meses (de 93) | 93 | 64 | 64 | 51 | 35 | 20 |
| % de tiendas grandes normales marcadas | 100 | 99 | 76 | 67 | 42 | 26 |
| **% de casos de tiendas normales enviados a CI** | 86.7 | 21.6 | 11.7 | **8.3** | 4.4 | 1.9 |
| **SKUs defectuosos detectados (de 3)** | 3 | 3 | 3 | **3** | 3 | 3 |
| Días para detectar un SKU defectuoso | 11 | 16 | 22 | 22 | 22 | 22 |
| SKUs normales marcados por mes | 28.0 | 8.0 | 0.9 | 0.9 | 0.9 | 0.9 |
| **Proveedor malo detectado** | Sí | Sí | Sí | **Sí** | Sí | Sí |
| Días para detectar el proveedor malo | 4 | 13 | 16 | 16 | 16 | 16 |
| Proveedores normales marcados en 12 meses | 47 | 15 | 10.5 | 10.5 | 10.5 | 10.5 |

## Lectura

1. **La lectura literal de la política (V0) no se puede operar.** El 88 % de los casos iría a CI, con 10 casos por día por país. Lo detecta todo porque marca todo.
2. **El defecto de V1 es usar umbrales fijos para todos.** Un SKU popular, un proveedor grande o una tienda grande llegan a 3, 5 o 6 casos por puro volumen. Por eso el 99 % de las tiendas grandes normales terminaba marcada y caían 8 SKUs normales por mes.
3. **Lo que corrige el problema es comparar cada uno contra su propia escala.** SKUs y proveedores se comparan contra su historia, y la tienda contra lo esperado para su tamaño. Además R1 cuenta solo lo imputable al proveedor, que es lo que indica un defecto de producto. Con eso la carga de R1 baja de 54 a 4.5 casos al mes **sin perder** ninguno de los SKUs defectuosos; se pierden ~6 días de velocidad de detección.
4. **R3b tiene que exigir acumulación.** Sin el mínimo de 3 casos, un solo caso caro dispara R3b, y eso ya lo cubre la matriz por caso (D1). Sin R3b no se encuentran las tiendas caras (0.4 de 2), así que R3b se queda.
5. **Entre R3b de 3 000 y de 5 000:** 3 000 detecta más tiendas caras (1.6 frente a 1.2 de 2) a cambio de 0.4 casos más por día para CI, unos 10 minutos diarios. **Recomiendo 3 000**: el costo es bajo, el patrón que encuentra es justamente el de fraude, y coincide con el monto de referencia de la política.
6. **El costo de V3 es la velocidad con las tiendas.** Una tienda que empieza a fallar tarda ~7 semanas en saltar. Es lento a propósito, para no castigar la mala suerte. Lo complementa la revisión mensual del tablero (concentración por reportante y por tienda) y las auditorías sorpresa de CI (9.3 de la política).
7. **"51 de 93 tiendas normales marcadas en el año"** no es tan grave como suena. Cada una aporta pocos casos a CI (el 8.3 % de los casos de tiendas normales) y funciona como una revisión aleatoria. Si CI lo percibe como ruido, la palanca es R3b = 5 000.

## Recomendación: V3 con α = 1 % y R3b = 3 000

| Regla | Criterio | Ventana |
|---|---|---|
| R1 — SKU + proveedor | Casos **imputables al proveedor** del mismo SKU ≥ máx(3, k₂.₅%(tasa propia del SKU)) | 60 días |
| R2 — Proveedor | Casos imputables al mismo proveedor ≥ máx(5, k₂.₅%(tasa propia del proveedor)) | 60 días |
| R3a — Tienda, frecuencia | Casos de la tienda ≥ k₁%(λ país × factor de tamaño de la tienda) | 30 días |
| R3b — Tienda, monto | ≥ 3 casos **y** costo acumulado ≥ USD 3 000 × máx(1, factor de tamaño) | 30 días |

**Esperado por país:** ~1.7 casos por día hábil a CI por recurrencia, que se suman a los casos de nivel 3 por monto.

## Limitaciones

- **Los datos son sintéticos.** Las distribuciones de tamaño, popularidad y costo son supuestos razonables, no datos de Unicomer. La conclusión cualitativa es robusta: los umbrales fijos fallan por volumen. Los números exactos no lo son.
- **Antes de pasar a `Aplicar`** hay que correr el simulacro sobre los datos reales del piloto. El siguiente paso es agregar al script la lectura del CSV exportado de la lista `Averías`.
- Los SKUs y proveedores **nuevos** no tienen historia: arrancan con el piso de 3 o 5, que es el comportamiento de V1 para ellos.
- **El factor de tamaño de tienda** sale de las ventas o unidades por tienda. Hay que cargarlo cada trimestre en `Cat_Ubicacion`, sin integración: se copia del BI de ventas.

## Cómo correrlo

```
python3 simulacro_recurrencia.py 30
```

Todos los supuestos están en el diccionario `SUPUESTOS`, al principio del script.
