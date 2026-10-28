# Workflow de averías — Unicomer ULA

Workflow para reportar, aprobar y cerrar averías en 6 países, con 1 CD por país y unas 100 tiendas cada uno.

El stack es SharePoint (lista `Averías`), Power Apps para la captura móvil, Power Automate para la aprobación y las notificaciones, y Power BI para la medición. Todo funciona con licencias M365 y conectores estándar, sin permisos de TI. **Power Apps no ajusta inventario:** el ajuste se sigue haciendo en Infor y la lista solo guarda el N.º de ajuste como evidencia para cerrar.

## Entregables

| # | Archivo | Contenido |
|---|---|---|
| 0 | [`00_contexto_politica.md`](00_contexto_politica.md) | **Política POL-CO-0031 v2.0**: reglas obligatorias, brechas del diseño actual y decisiones abiertas (D1–D8). **Leer primero: los documentos 01–05 todavía no están alineados con la política.** |
| 1 | [`01_esquema_lista.md`](01_esquema_lista.md) | Columnas, tipos, validaciones, índices, máquina de estados y listas de soporte |
| 2 | [`catalogos/`](catalogos) | `tipo_averia.csv`, `causa.csv`, `ubicacion.csv` |
| 3 | [`03_reglas_aprobacion.md`](03_reglas_aprobacion.md) + [`config/`](config) | Umbrales por costo, escenarios A/B/C, SLA, anti-fraccionamiento, segregación y parámetros editables |
| 4 | [`04_medidas_dax.md`](04_medidas_dax.md) | Power Query, modelo, medidas DAX y RLS por país |
| 5 | [`05_flujo_power_automate.md`](05_flujo_power_automate.md) | Flujos AV-01 a AV-04 paso a paso, con expresiones y casos de prueba |

Los CSV están en UTF-8 con BOM para que Excel muestre bien las tildes, y sirven para **Nueva lista → Desde CSV** en SharePoint.

## Decisiones de diseño (y por qué)

1. **El reportante no digita el costo.** El costo sale de Infor y lo carga Control de Inventarios en el paso de valorización, después de N1. El tramo de aprobación depende del costo, así que si lo digita quien reporta el control se puede burlar. Además, Control de Inventarios es quien después registra el ajuste, de modo que valorizar no le suma un rol nuevo.
2. **El umbral se calcula sobre el costo bruto en USD** y sobre el acumulado de 7 días del mismo SKU en la misma ubicación (anti-fraccionamiento). El valor recuperable no cuenta para el umbral.
3. **Todas las averías pasan por N1; no hay autoaprobación.** El control de los montos chicos lo hace Power BI con análisis de concentración, no más firmas.
4. **Umbrales: escenario B** (N2 ≥ $250, N3 ≥ $1 000, N4 ≥ $5 000). Según los supuestos de [`03_reglas_aprobacion.md`](03_reglas_aprobacion.md), cubre ~88 % del costo con N2 revisando ~20 % de los casos. Se recalibra al mes 3 con datos reales.
5. **El cierre no espera el cobro del reclamo.** Cierre = ajuste en Infor + evidencia de la disposición. La recuperación se mide aparte.
6. **El KPI principal de cierre es `% cumplimiento SLA cierre` (por cohorte de vencimiento)**, no `% cerrado a tiempo`, porque el segundo mejora cuando no se cierra nada.
7. **Una sola lista regional** con `PaisCodigo`. No se usan permisos por ítem; la app filtra por país y Power BI aplica RLS. Es una limitación aceptada.

## Prerrequisitos que hay que confirmar antes de construir

- [ ] **Licencias del personal de tienda y CD.** Cada reportante necesita una cuenta M365 con acceso a SharePoint y Power Apps para M365. Si el personal de tienda no tiene cuenta, el reportante pasa a ser el jefe de tienda y cambia el diseño de N1.
- [ ] **Power BI Pro** para quien publica y para los gerentes de país que consumen.
- [ ] **Sitio de SharePoint** del que Logística regional sea propietaria.
- [ ] **El país 6:** figura como `P6` en los catálogos; hay que confirmar el código, la moneda y la zona horaria.
- [ ] **El maestro de tiendas de Infor** (código, nombre, CD abastecedor y código Infor), para reemplazar las filas de ejemplo de `ubicacion.csv`.
- [ ] **Los motivos de ajuste de Infor por disposición** (tabla en `05_flujo_power_automate.md`), definidos por Control de Inventarios de cada país.
- [ ] **Aprobadores y suplentes por rol, país y ubicación** (`config/aprobadores_plantilla.csv`).

## Orden de implementación sugerido

1. Crear el sitio, las listas de soporte desde los CSV y la lista `Averías`, con los nombres internos primero y los índices antes de cargar datos.
2. Construir AV-01 a AV-03 en una lista de prueba y correr los casos de prueba del documento 05.
3. Hacer la app de Power Apps con cuatro pantallas: Reportar, Mis averías, Aprobar/Valorizar y Cerrar (ajuste Infor). La app no forma parte de este paquete.
4. Hacer un piloto en un país (1 CD + 10 tiendas) durante 4 semanas, con AV-04 y el tablero de Power BI.
5. Hacer el despliegue regional y recalibrar los umbrales al mes 3 con la simulación del documento 04.
