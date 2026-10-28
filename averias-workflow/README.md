# Workflow de averías — Unicomer ULA

Es el procedimiento digital de la **Política de Averías POL-CO-0031 v2.0** para 6 países, con 1 CD por país y unas 100 tiendas en cada uno.

El stack es SharePoint (listas `Averías` y `Averías_Lineas`), Power Apps para la captura móvil, Power Automate para la aprobación, la disposición y las notificaciones, y Power BI para los KPIs de la política. Todo funciona con licencias M365 y conectores estándar, **sin permisos de TI**. **Power Apps no ajusta inventario:** los movimientos se siguen registrando en Infor, y el workflow solo guarda el número como evidencia para cerrar.

## Entregables

| # | Archivo | Contenido |
|---|---|---|
| 0 | [`00_contexto_politica.md`](00_contexto_politica.md) | Resumen de la política, cambios aplicados, huecos D1–D8 con la decisión del procedimiento y la regla de recurrencia (D2) |
| 1 | [`01_esquema_lista.md`](01_esquema_lista.md) | Encabezado + líneas, columnas, validaciones, índices, máquina de estados y listas de soporte |
| 2 | [`catalogos/`](catalogos) | `tipo_averia.csv` (los 6 tipos oficiales), `subtipo.csv`, `causa.csv` (por origen) y `ubicacion.csv` |
| 3 | [`03_reglas_aprobacion.md`](03_reglas_aprobacion.md) + [`config/`](config) | Matriz 7.3 aplicada, autorización de la disposición, SLA, escenarios de carga por aprobador y parámetros |
| 4 | [`04_medidas_dax.md`](04_medidas_dax.md) | Modelo de Power BI, **todos los KPIs de la sección 9**, control del procedimiento y RLS |
| 5 | [`05_flujo_power_automate.md`](05_flujo_power_automate.md) | Flujos AV-01 a AV-05 paso a paso y 20 casos de prueba |
| 6 | [`06_power_apps.md`](06_power_apps.md) | App móvil: 8 pantallas, bandeja "Mis pendientes", fórmulas Power Fx delegables y pruebas |
| — | [`simulacion/`](simulacion) | Simulacro de la recurrencia ([`RESULTADOS.md`](simulacion/RESULTADOS.md)) y de la carga por aprobador (`carga_matriz.py`) |

Los CSV están en UTF-8 con BOM, para que Excel muestre bien las tildes, y sirven para **Nueva lista → Desde CSV**.

## Flujo en una línea

Reporte (≤ 24 h) → valorización CI (costo y retail de Infor) → nivel según la matriz y la recurrencia → aprobación (≤ 48 h, un aprobador) → diagnóstico ST si aplica → disposición autorizada por su dueño (Gerente de Producto 72 h, CI o Compras) → movimiento Infor + evidencia → cierre.

## Decisiones de diseño

1. **El costo lo carga CI desde Infor, no el reportante.** La matriz depende del costo unitario, y si lo digitara quien reporta podría elegir quién le aprueba. Quien valoriza no puede aprobar el N3.
2. **Matriz de la política con tres precisiones del procedimiento:**
   - El caso de más de USD 3 000 va a N3 [D1].
   - El unitario de referencia es el máximo de las líneas [D3].
   - Bodega externa y 3PL usan la matriz del CD; la última milla usa la de la tienda vendedora [D7].
3. **Recurrencia relativa, no con umbrales fijos** [D2]: cada SKU y cada proveedor se comparan contra su propia historia, y la tienda contra lo esperado para su tamaño. Con umbrales fijos, el simulacro mandaba a CI el 49 % de los casos; con la regla relativa, ~1.7 casos por día por país, y detecta todas las anomalías plantadas.
4. **La disposición física y la recuperación van por separado:** un mismo caso puede ir a outlet **y** cobrarse al transportista a precio retail.
5. **El cierre no espera el cobro.** Cierre = movimiento Infor + evidencia de la disposición. La recuperación se mide aparte.
6. **Todo dentro del ticket** [8.2.4–8.2.5]: Teams solo notifica; las decisiones quedan en Approvals o en la app, con bitácora e historial.
7. **Una sola lista regional** con `PaisCodigo`. La app filtra por país y Power BI aplica RLS.

## Prerrequisitos que hay que confirmar antes de construir

- [ ] **Licencias M365 del personal de tienda, CD y ST.** Sin cuenta no pueden reportar ni diagnosticar en la app.
- [ ] **Power BI Pro** para quien publica el tablero y para quienes lo consumen.
- [ ] **Sitio de SharePoint** del que Logística regional sea propietaria, con la biblioteca `BI_Externos`.
- [ ] **El país 6** (`P6`): código, moneda y zona horaria.
- [ ] **Maestro de tiendas de Infor** con el `FactorTamano` (ventas de los últimos 3 meses de cada tienda ÷ el promedio del país).
- [ ] **Códigos de motivo de movimiento Infor** por disposición, definidos por CI de cada país.
- [ ] **Aprobadores y suplentes** por rol: Gerente de Tienda, Operaciones local, Gerente de Logística CD, CI valorizador, CI aprobador, Gerente de Producto, Compras, Finanzas y Seguros, ST.
- [ ] **Capacidad de CI:** en el escenario base, ~40 min/día de valorización + 3.5 casos N3/día por país. Con volumen alto puede llegar a 13 casos/día, y entonces hace falta un analista dedicado (ver 03 §4).
- [ ] **Exportes mensuales a `BI_Externos`:** ventas netas, inventario promedio y recepciones por proveedor.

## Orden de implementación sugerido

1. Crear el sitio, las listas de soporte desde los CSV y las listas `Averías` y `Averías_Lineas`, con los nombres internos primero y los índices antes de cargar datos.
2. Construir AV-01 a AV-04 en una lista de prueba y correr los 20 casos de prueba del documento 05.
3. Construir la app según [`06_power_apps.md`](06_power_apps.md) y correr sus pruebas.
4. Hacer el piloto en un país (1 CD + 10 tiendas) durante 4 semanas, con `RecurrenciaModo = Observar`, AV-05 y el tablero.
5. Correr el simulacro con los datos reales del piloto, pasar a `Aplicar` y hacer el despliegue regional.
6. Recalibrar al mes 3: λ del país, `FactorTamano` y las señales del documento 03 §4.
