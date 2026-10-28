# 03 — Reglas de aprobación y disposición

Alineado con **POL-CO-0031 v2.0**. Los montos y los aprobadores salen de la política (7.3); este documento define **cómo** se aplican (el procedimiento, 1.2) y resuelve los huecos D1–D8 de [`00_contexto_politica.md`](00_contexto_politica.md).

## 1. Matriz de aprobación de la avería

Un solo aprobador por nivel, sin cadena acumulativa. Los montos son a **costo de adquisición en USD** [7.3.1].

### Averías con matriz Tienda (tienda y última milla) [7.3.2]

| Nivel | Condición | Aprueba |
|---|---|---|
| N1 | Costo unitario máximo ≤ USD 100 **y** caso ≤ USD 3 000 **y** sin recurrencia | Gerente de Tienda (en última milla, el de la tienda vendedora) |
| N2 | Unitario > 100 y ≤ 600 **y** caso ≤ USD 3 000 **y** sin recurrencia | Operaciones local, como instancia independiente |
| N3 | Unitario > 600, **o** caso > USD 3 000 [D1], **o** recurrencia | Control de Inventarios — Aprobador |

### Averías con matriz CD (CD, bodega externa y 3PL) [7.3.3, D7]

| Nivel | Condición | Aprueba |
|---|---|---|
| N1 | Unitario ≤ 100 **y** caso ≤ USD 3 000 **y** sin recurrencia | Gerente de Logística del CD |
| N3 | Unitario > 100, **o** caso > USD 3 000 [D1], **o** recurrencia | Control de Inventarios — Aprobador, **sin intervención de Operaciones** |

### Reglas de cálculo

- **Costo unitario de referencia:** el **máximo** costo unitario entre las líneas del caso [D3].
- **Costo del caso:** la suma de todas sus líneas [D8].
- **Límites:** "hasta USD 100" incluye el 100 (N1). "Entre 100 y 600" va de 100.01 a 600. Más de 600 es N3.
- **D1 (caso > USD 3 000 → N3):** también se aplica en el CD, por coherencia. Sin esa regla, 40 unidades de USD 90 las aprobaría solo el gerente. Se configura con `CasoMaxSinNivel3USD`.
- **Recurrencia:** usa las reglas R1, R2, R3a y R3b validadas en el simulacro (ver D2 en `00_contexto_politica.md`). En modo `Observar` (las 4 primeras semanas del piloto) solo se marca `RecurrenciaObservada` y el nivel no cambia.
- **Motivo del nivel:** el caso se marca con todos los motivos que apliquen (`MotivoNivel`), para que el aprobador sepa por qué le llegó.
- **Regla congelada:** `VersionMatriz` se escribe al enrutar. Un cambio de matriz solo afecta a los casos nuevos.

### Segregación

- El aprobador no puede ser el reportante.
- El aprobador de N3 (CI) no puede ser quien valorizó el caso.
- Si hay conflicto, el caso va al **suplente** del rol. Si el suplente también tiene conflicto, va al suplente de CI y se avisa al Gerente de Logística del país.
- **D6:** los casos de la matriz CD con costo > `NotificarRegionalCasoUSD` (USD 3 000) se **notifican** al Gerente de Logística regional. Es solo información: la política no le da un nivel de aprobación.

## 2. Autorización de la disposición [7.4–7.8]

Después de aprobada la avería, la disposición física tiene su propio dueño según la política:

| Disposición | Requisito previo | Autoriza | SLA | Evidencia para cerrar |
|---|---|---|---|---|
| Reincorporación (reparación ST) | `DiagnosticoST = Reparable` o `Sin falla` [7.5.1] | Sin autorización adicional. El Gerente de Logística o de Tienda coordina el traslado a ST [3-#4] | — | Comprobante de reincorporación en Infor después de la reparación y la prueba [7.5.3] |
| Venta con descuento (outlet / remate) | — | **Gerente de Producto**, que carga el % de descuento [7.6.1] | **72 h** [3-#5] | N.º de traslado a outlet en Infor |
| Devolución a proveedor local | Origen = Proveedor local [7.7.1] | **Compras** confirma que procede según las condiciones comerciales [7.7.2.2] | 48 h | Guía de devolución y N.º de salida Infor. La NC se sigue aparte |
| Devolución a proveedor internacional | Origen = Proveedor importado [7.7.1] | **Compras** (condiciones comerciales), con aviso a Finanzas para la provisión [7.7.3] | 48 h | Documento de NC, ajuste o compensación |
| Destrucción | No apta para reparación ni venta [7.8.1] | **Control de Inventarios** valida antes [7.8.1] | 48 h | **Acta formal** y fotos [7.8.2], y N.º de ajuste Infor |
| Donación | Igual que destrucción, más contrato si aplica [7.8.2] | **Control de Inventarios** | 48 h | Acta y contrato de donación, y N.º de ajuste Infor |

**Diagnóstico técnico obligatorio** [7.2.1] cuando el tipo de avería es **TP5 (falla técnica o funcional)** o la disposición propuesta es **Reincorporación**. Si el diagnóstico es "No reparable", la app no deja elegir Reincorporación.

**La recuperación va por una vía paralela y no bloquea el cierre:**
- Cobro a transportista u OPL **a precio retail** [5.2.1.4] → se avisa a **Finanzas y Seguros** con `MontoFacturableUSD = RetailTotalUSD`.
- Nota de crédito o compensación del proveedor → **Compras**.
- Reclamo a aseguradora → **Finanzas y Seguros**.

## 3. SLA del procedimiento

| Paso | SLA | Fuente |
|---|---|---|
| Reporte desde la detección | **24 h** | Política 8.2.1 |
| Valorización (CI) | 24 h | Procedimiento |
| Aprobación de la avería, cada nivel | **48 h** (recordatorio a las 24 h, suplente a las 40 h) | Política 3, 8.2.2 |
| Diagnóstico ST | 5 días | Procedimiento |
| Autorización de venta con descuento | **72 h** | Política 3, 7.6 |
| Validación de destrucción o donación / confirmación de RTV | 48 h | Procedimiento |
| Ejecución (movimiento Infor y evidencia) | 3 días | Procedimiento |
| **Cierre E2E** (detección → disposición final) | N1: 10 días · N2: 15 días · N3: 20 días | Procedimiento (`SLACierreDias` en `Cfg_Matriz`) |

**Por qué el suplente entra a las 40 h y no a las 48 h:** escalar en la hora 48 significa que el SLA ya se incumplió. Con 40 h el suplente tiene 8 h para responder dentro del plazo.

Los SLA del procedimiento que no fija la política son **parámetros** en `Cfg_Parametros` o `Cfg_Matriz`.

## 4. Escenarios de carga por aprobador

La matriz ya la fija la política, así que la incertidumbre está en **cuánto trabajo le genera a cada rol**. Esa carga depende de dos cosas que todavía no sabemos: el costo unitario típico de las averías y el volumen. Calculado con `simulacion/carga_matriz.py`, que aplica la matriz y la recurrencia V3 a 10 corridas del país sintético.

**Casos por día hábil, por país:**

| Escenario | Casos/mes | Gerente de Tienda (N1, entre las 100 tiendas) | Operaciones local (N2) | CI tienda (N3) | Gerente Logística CD | CI CD | **CI total** | Parte de CI que llega por recurrencia |
|---|---|---|---|---|---|---|---|---|
| 2 casos/tienda/mes · unitario mediano USD 100 | 258 | 4.3 | 4.0 | 1.5 | 0.9 | 1.1 | **2.6** | 44 % |
| **2 · USD 150 (base)** | 258 | 2.9 | 4.7 | 2.2 | 0.6 | 1.3 | **3.5** | 37 % |
| 2 · USD 250 | 258 | 1.4 | 4.8 | 3.6 | 0.3 | 1.6 | **5.2** | 30 % |
| 4 · USD 100 | 505 | 8.0 | 7.3 | 3.9 | 1.8 | 2.0 | **5.9** | 53 % |
| 4 · USD 150 | 505 | 5.0 | 8.1 | 6.1 | 1.2 | 2.5 | **8.6** | 50 % |
| 4 · USD 250 | 505 | 2.2 | 6.9 | 10.1 | 0.6 | 3.1 | **13.3** | 46 % |

### Lectura

- **El Gerente de Tienda casi no carga trabajo** (~0.03 casos por tienda por día). El trabajo real cae en **Operaciones local y CI**.
- **Con la matriz de la política, la mayoría de los casos de tienda va a Operaciones (N2):** con una mediana de USD 150 por unidad, más de la mitad de las averías pasa de USD 100 por unidad. Operaciones local recibe ~5 casos por día por país en el escenario base y ~8 en el de alto volumen. Si Operaciones local es **una sola persona por país**, hay que asignarle un suplente formal desde el día 1.
- **CI tiene dos cargas:**
  - **Valorizar todos los casos:** ~12 por día en el escenario base, a 2–3 minutos cada uno (~40 min/día).
  - **Aprobar los N3:** entre 3.5 y 13 por día. A ~10 minutos por caso, eso va de 35 minutos a más de 2 horas diarias.
  - **Con más de 6 casos N3 por día, CI necesita un analista con tiempo asignado a averías.** De lo contrario el SLA de 48 h no se cumple.
- **La recurrencia aporta entre el 30 % y el 50 % de la carga de CI.** Es la palanca configurable si CI se satura: bajar `RecTienda_Alfa` a 0.005 o subir `RecTienda_MontoUSD` a 5 000, sin tocar la matriz de la política.

### Señales para revisar (al mes 3 del piloto)

| Señal en Power BI | Acción |
|---|---|
| CI recibe > 6 casos N3 por día hábil durante 4 semanas | Asignar un analista dedicado y ajustar la recurrencia (`RecTienda_Alfa`, `RecTienda_MontoUSD`) |
| Mediana de aprobación de Operaciones local > 24 h | Suplente formal o división por zona (`Cfg_Aprobadores` por ubicación) |
| Amontonamiento de casos con unitario de USD 90–100 (> 1.5 veces los de USD 100–110) | Posible ajuste de precios para quedar en N1: auditoría de CI a esas tiendas |
| % de rechazo en N2 < 2 % sostenido | El nivel no está agregando control: llevarlo a la revisión de la política (2027-05) |
| Casos de la matriz CD > USD 3 000 frecuentes | Proponer en la revisión de la política un nivel superior para el CD (D6) |

## 5. Parámetros

| Lista | Qué se configura |
|---|---|
| `Cfg_Matriz` | Niveles, rangos unitarios, rol aprobador, SLA de aprobación y de cierre por nivel. Los cambios se versionan (`Version`, `VigenteDesde`, `VigenteHasta`); **los montos cambian solo si cambia la política** |
| `Cfg_Parametros` | D1 (`CasoMaxSinNivel3USD`), D6, SLA del procedimiento, recordatorios y escalamiento, y todos los parámetros de recurrencia |
| `Cfg_Aprobadores` | Persona y suplente por rol, país y ubicación |
| `Cfg_TablaPoisson` | k por λ para la recurrencia (fija) |
| `Cat_Ubicacion` | `FactorTamano` y `KRecurrenciaTienda`, actualizados cada trimestre |
