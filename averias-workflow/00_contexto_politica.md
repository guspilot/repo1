# 00 — Contexto: Política de Averías POL-CO-0031

## Fuente

| | |
|---|---|
| Documento | POL-CO-0031 — Política de Averías de Mercadería (Grupo Unicomer) |
| Versión usada | **2.0** (encabezados de página: fecha 2026/07/01) |
| Ubicación | SharePoint *Transformación* → Procesos E2E → Políticas Corporativas BEM → 1. Políticas Vigentes (Formato Editable) → R2RE → `POL-CO-0031-Política de Averías.docx` (modificado el 2026-09-23) |
| Dueño del proceso (BPO) | Fernando Marín, COO |
| Autor y líder del proceso | Gustavo Ocampo, Gerente Corporativo de Logística ULA |
| Próxima revisión | 2027/05/01 |

> **Inconsistencias de versión dentro del mismo archivo:** la portada dice v1.0 (vigor 2026/05/01, modificación 2025/09/16), los encabezados de página dicen v2.0 con fecha 2026/07/01, la sección 11 dice V1.0 y el registro de cambios fecha la v2.0 el 26/06/18. Conviene corregirlo en la próxima publicación.

**Alcance del documento (1.2):** la política define el *qué*. El procedimiento lo define cada país, cumpliendo la política y adaptándolo a sus sistemas y regulación. **Este workflow es ese procedimiento operativo, así que no puede contradecir la política; puede ser más específico.**

## Reglas de la política que el workflow tiene que cumplir

### Sistema y trazabilidad
- **7.1–7.2:** toda gestión de averías se hace **exclusivamente** en el sistema corporativo de workflow digital, desde la clasificación hasta la disposición final, y con control de SLA entre áreas.
- **8.2.4:** está **prohibido** aprobar o gestionar averías con firma manual, correo, mensajes o cualquier medio fuera del workflow.
- **8.2.5–8.2.6:** toda comunicación y seguimiento se registra **dentro del ticket**, junto con todas las acciones, desde la detección hasta la reparación, la disposición o el reclamo.

### Plazos (SLA)
| Paso | Plazo | Responsable | Sección |
|---|---|---|---|
| Reportar desde la detección | **≤ 24 h** | Personal de almacén y tienda | 3, 8.2.1 |
| Aprobar o rechazar, cada nivel | **≤ 48 h** | Aprobador del nivel | 3, 8.2.2 |
| Autorizar descuento para venta de mercadería averiada | **≤ 72 h** | Gerente de Producto | 3, 7.6.1 |

### Contenido obligatorio del reporte (8.2.2)
Clasificación del origen, tipo de desperfecto, resumen descriptivo, **SKU y número de serie**, y evidencia (fotos o videos). Además, el producto se **consolida en la ubicación física designada para averías** (3, 5.4.5).

### Matriz de aprobación (7.3)
Se calcula sobre el **costo de adquisición**, no sobre el precio de venta (7.3.1).

**Averías originadas en tienda (7.3.2):**
| Nivel | Criterio | Aprueba |
|---|---|---|
| 1 | Hasta USD 100 **por unidad** | Gerente de Tienda |
| 2 | USD 100–600 por unidad, **o** hasta USD 3 000 por caso o lote consolidado | **Operaciones local**, como instancia independiente |
| 3 | Más de USD 600 por unidad, **o** recurrencia del mismo SKU, proveedor o tienda en 30–60 días | Control de Inventarios |

**Averías originadas en el CD (7.3.3):**
| Nivel | Criterio | Aprueba |
|---|---|---|
| 1 | Hasta USD 100 por unidad | Gerente de Logística del CD |
| 2 y 3 | Más de USD 100 por unidad, o recurrencia | Control de Inventarios, **sin intervención de Operaciones** |

Lectura de la matriz: **un solo aprobador por nivel**, no una cadena acumulativa. Cada nivel tiene un dueño distinto.

### Disposición (7.4–7.8)
| Disposición | Condición o paso obligatorio | Quién |
|---|---|---|
| Reincorporación al inventario | Solo si la avería es reparable: traslado a la bodega designada y envío a ServiTotal/Servitech con comprobante digital del movimiento. Reparado y probado, se reincorpora según la política de garantías | Logística, ST, Finanzas (registro contable) |
| Venta con descuento (outlet o tienda de remate) | Autorización en el workflow; Comercial valida la marca y el precio | **Gerente de Producto (72 h)**, Comercial |
| Devolución a proveedor local | Solo si la avería es atribuible al proveedor; devolución física; registro en el sistema y nota de crédito | Compras |
| Devolución a proveedor internacional | Si la devolución física no es viable: condiciones comerciales (NC, compensación) y tratamiento contable de la provisión | Compras, Finanzas |
| Destrucción o donación | Solo si el producto no se puede reparar ni vender, con **validación previa de Control de Inventarios**, acta formal, contrato si aplica, fotos y cumplimiento legal local | Control de Inventarios, Finanzas |
| Diagnóstico técnico | ServiTotal/Servitech diagnostica las averías recopiladas en tiendas y CD | ST (7.2.1) |
| Cobro al transportista | **A precio retail**, no a costo, salvo que la ley local indique otra cosa | Finanzas y Seguros (5.2.1.4) |

### Clasificaciones oficiales
**Tipo de avería (4.1):** Daño de empaque · Daño físico de producto · Daño por manipulación · Daño por condiciones ambientales · Fallas técnicas o funcionales · Otros daños específicos (incluye productos incompletos o con piezas faltantes).

**Tipo de responsable (6.2):** Proveedor local · Proveedor importado · Transporte propio · Transporte tercerizado · Centro de Distribución · Bodega externa · 3PL / operador logístico externo · Tienda · Proceso de entrega al cliente final.

### KPIs obligatorios (9.1–9.2)
| KPI | Fórmula de la política | ¿Se calcula solo con la lista? |
|---|---|---|
| Costo de averías vs. ventas netas | Costo total de averías ÷ ventas netas × 100 | No: necesita ventas netas por país y mes |
| Índice general de averías | Valor retail y costo averiado ÷ valor movilizado (sobre el inventario promedio mensual) × 100 | No: necesita el inventario promedio de Infor |
| Tiempo de resolución E2E | Σ días desde la **detección** hasta la disposición final ÷ averías resueltas | Sí |
| Índice por tipo y origen | Valor de averías con origen X y tipo Y ÷ valor total × 100 | Sí |
| % de inventario averiado consolidado | Valor consolidado ÷ valor reportado × 100 | Sí, si se agrega el registro de consolidación |
| Tiempo de reporte promedio | Σ horas desde la detección hasta el reporte ÷ averías reportadas | Sí, si la detección se guarda **con hora** |
| Tiempo de aprobación promedio | Σ horas de aprobación ÷ averías aprobadas | Sí |
| Rotación de inventario averiado | Costo vendido con avería ÷ inventario averiado promedio | Parcial: necesita las ventas outlet |
| % de recuperación de costos | Monto recuperado ÷ monto **facturable** × 100 | Sí, si se agrega el monto facturable |
| Tasa de averías por proveedor | Unidades averiadas del proveedor ÷ unidades recibidas del proveedor × 100 | No: necesita las recepciones de Infor |
| Recurrencia por SKU | N.º de incidentes del mismo SKU y proveedor en 30–60 días | Sí |
| Tasa de cumplimiento de la política | Hallazgos ÷ auditorías, separando proceso de inventario no declarado | No: viene de las auditorías de CI |

Las métricas se presentan en un **tablero corporativo en tiempo real**, revisado mensualmente (9.3).

---

## Impacto sobre el diseño actual (documentos 01–05)

Partes del diseño que hice antes de leer la política **no cumplen** y hay que cambiarlas:

| # | Diseño actual | Lo que exige la política | Cambio |
|---|---|---|---|
| 1 | Tramos sobre el **costo total del caso**, cadena acumulativa N1→N4 (jefe → gerente de operación → gerente de logística país → regional) y escenarios A/B/C | Niveles por **costo unitario** (USD 100 / 600) y por caso (USD 3 000), un solo aprobador por nivel, **matriz distinta para tienda y CD** | Rehacer `Cfg_Umbrales` y AV-02 con la matriz 7.3. Se eliminan N4 regional y el gerente de logística país como aprobadores. Los escenarios A/B/C dejan de aplicar a los montos, que ya fija la política |
| 2 | Anti-fraccionamiento: mismo SKU y ubicación en 7 días, sube un tramo | Recurrencia del mismo **SKU, proveedor o tienda** en 30–60 días lleva a nivel 3 (Control de Inventarios) | Reemplazar por la regla de recurrencia (ver decisión D2) |
| 3 | El reporte puede llegar hasta 3 días después de la detección | **≤ 24 h** | `MaxHorasDeteccionAReporte = 24`; `FechaDeteccion` pasa a **fecha y hora** |
| 4 | SLA de aprobación de 24 h por nivel, con escalamiento a las 48 h | **48 h** por nivel | SLA = 48 h, recordatorio a las 24 h y escalamiento al suplente a las 48 h |
| 5 | `ResponsableImputable`: Proveedor, Transportista, Operación CD, Tienda, Cliente, Aseguradora | 9 tipos oficiales (6.2) | Reemplazar los valores de la elección por los 9 tipos de la política. La aseguradora pasa a ser una **vía de recuperación**, no un responsable |
| 6 | 14 tipos de avería propios | 6 tipos oficiales (4.1) | `TipoAveria` = los 6 tipos de la política, obligatorio. Los 14 actuales pasan a `Subtipo` opcional para el análisis de causa raíz |
| 7 | `NumeroSerie` obligatorio solo para fallas funcionales | SKU **y número de serie** obligatorios | Obligatorio siempre, con un valor `SIN SERIE` permitido para muebles, colchones y otros productos sin serie (ver D4) |
| 8 | Solo costo | La materialidad se mide a costo; el cobro al transportista se hace a **retail**; los KPIs usan retail **y** costo | Agregar `PrecioRetailUnitarioLocal` y `ValorRetailUSD` |
| 9 | La disposición la aprueba la misma cadena | Venta con descuento: **Gerente de Producto en 72 h**. Destrucción o donación: **validación previa de CI** con acta | Agregar el paso de **autorización de disposición** después de la aprobación de la avería (nuevo flujo o rama de AV-02) |
| 10 | Sin consolidación física | Consolidar en la ubicación de averías es obligatorio y además es un KPI | Agregar `Consolidado` (Sí/No), `FechaConsolidacion` y `UbicacionConsolidacion` |
| 11 | No se registra el diagnóstico técnico | ServiTotal/Servitech diagnostica | Agregar `DiagnosticoST` y `FechaDiagnosticoST`; obligatorios para las fallas técnicas antes de decidir la disposición |
| 12 | El tiempo de resolución corre desde el envío | E2E desde la **detección** hasta la disposición final | Medida DAX E2E desde `FechaDeteccion`; se conserva además la medida desde el envío como indicador operativo |
| 13 | `MontoRecuperadoUSD` solamente | % de recuperación = recuperado ÷ **facturable** | Agregar `MontoFacturableUSD`, que se calcula a retail cuando el responsable es un transporte y según el acuerdo comercial cuando es un proveedor |
| 14 | Ubicaciones: CD, Tienda, Tránsito, Última milla | También bodega externa y 3PL | Agregar los tipos `Bodega externa` y `3PL` a `Cat_Ubicacion` |
| 15 | Notificaciones por Teams y aprobación con Approvals | Prohibido gestionar fuera del workflow | **Compatible:** Approvals registra la respuesta dentro del workflow y la copia al ticket (historial y comentarios). Teams solo **notifica**; la regla operativa es que ninguna decisión se toma por chat o correo |

Lo que **ya cumple**: el workflow único digital y móvil, la trazabilidad en `Averias_Historial`, la valorización a costo de Infor (coincide con 7.3.1 "costo de adquisición"), el cierre ligado a la disposición final, la segregación (coincide con "Operaciones como instancia independiente") y la evidencia fotográfica obligatoria.

## Huecos de la propia política que el procedimiento tiene que resolver

Como sos el autor de la política, estas decisiones son tuyas. Para cada una dejo mi recomendación.

| # | Hueco | Riesgo | Recomendación para el procedimiento |
|---|---|---|---|
| **D1** | Tienda: si el costo unitario es ≤ 100 pero el caso pasa de 3 000 (p. ej. 40 u × USD 90 = USD 3 600), ¿qué nivel corresponde? El nivel 2 dice "hasta USD 3 000 por caso", pero nada lleva un caso grande a nivel 3 | Un gerente de tienda aprueba solo pérdidas de miles de dólares si son muchas unidades baratas | Nivel = **el mayor** entre el nivel por unitario y el nivel por caso. Caso ≤ 3 000 y unitario ≤ 100 → N1; caso > 3 000 → N3 |
| **D2** | "Recurrencia del mismo SKU, proveedor **o tienda** en 30–60 días" sin un umbral de cantidad. Con ~100 tiendas que reportan varias averías al mes, casi **todo** caso de tienda sería "recurrente" | Control de Inventarios recibe prácticamente todo el volumen y se vuelve el cuello de botella. El 48 h se incumple desde el día 1 | Recurrencia = **≥ 3 incidentes** del mismo SKU + proveedor, o **≥ N casos o USD X** de la misma tienda, en **60 días**. Que sean parámetros en `Cfg_Parametros` y se calibren con el piloto |
| **D3** | "Costo unitario" cuando el caso tiene varias líneas o SKU | Ambigüedad sobre qué unitario usar | Usar el **máximo** costo unitario de las líneas del caso |
| **D4** | Número de serie obligatorio para todo, cuando muebles y colchones no tienen | El reportante inventa un valor o abandona el reporte | Permitir `SIN SERIE` solo para las categorías sin serie (lista en el catálogo de subtipos) |
| **D5** | 8.2.2 remite a la matriz en la "sección 7.1" (está en 7.3), y 8.2.3 repite 8.2.2 pero solo nombra al gerente de CD o tienda como aprobadores | Contradicción en una auditoría | Corregir en la próxima revisión: 8.2.2 → 7.3 y eliminar 8.2.3 |
| **D6** | CD: "2 y 3 aprueba Control de Inventarios" desde USD 100 por unidad, sin tope superior | CI de cada país aprueba todo lo del CD > 100 u., incluidas pérdidas grandes, sin una instancia superior | Aceptable según la política. Sugiero, como **notificación** y no como aprobación, avisar al Gerente de Logística regional de los casos > USD 3 000, para no contradecir la matriz |
| **D7** | Averías en tránsito, en última milla, en bodega externa o en 3PL: la matriz solo define "originadas en tienda" y "originadas en CD" | Casos sin regla | Mapear por **dónde se detecta**: tránsito CD→tienda detectado en la tienda usa la matriz de tienda; bodega externa y 3PL usan la matriz de CD; última milla usa la matriz de tienda (la tienda vendedora) |
| **D8** | ¿Un caso es una línea o un lote? La política habla de "caso o lote consolidado" | Define el monto del criterio de USD 3 000 | Ticket = **1 evento con N líneas** (SKU, cantidad, serie). El monto del caso = Σ líneas. Implica separar la lista en dos: `Averias` (encabezado) y `Averias_Lineas` |

> D8 cambia el modelo de datos: hoy cada ítem es un solo SKU. En tu presentación `workflow_averias_v2_ES.pptx` (OneDrive, mayo de 2026) ya planteabas "1 evento · N líneas · SKU · origen", que es consistente con esta recomendación.

## Otras fuentes encontradas (no leídas a fondo)

- Notion → Torre de Control de Proyectos → **App de Averias** (proyecto con minutas y matriz de riesgos).
- Notion → Wiki Logística → **Averías** (diagrama de flujo, excepciones y escalación).
- OneDrive → `workflow_averias_v2_ES.pptx` (presentación del workflow, v1.0, mayo de 2026).
- OneDrive → `averias analisis.docx` (análisis del borrador anterior POL.000028).
- Versiones **no vigentes**: `POL 000031_Politica de Averías.docx` (archivo de políticas no vigentes) y el Google Doc "Política de Manejo de Averías y Daños (v. 2.4)" de 2025. No se usaron.
