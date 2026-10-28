# 01 — Esquema SharePoint: listas "Averías", "Averías_Lineas" y soporte

Alineado con **POL-CO-0031 v2.0** (ver [`00_contexto_politica.md`](00_contexto_politica.md)). Las referencias entre corchetes, como [7.3], son secciones de la política; [D1]…[D8] son las decisiones del procedimiento.

## Regla de oro antes de crear columnas

El **nombre interno** de una columna se fija al crearla y no cambia nunca, y Power Automate, Power Apps y Power BI usan ese nombre. Por eso:

1. Creá cada columna con el **nombre interno de la tabla**: sin tildes, sin espacios, sin ñ.
2. Después renombrala con el **nombre visible**.

Si la creás como "Fecha de aprobación", el nombre interno queda `Fecha_x0020_de_x0020_aprobaci_x00f3_n` y rompe las fórmulas en los tres productos.

## Sitio y permisos (sin TI)

- **Un sitio** del que Logística regional sea propietaria. Crear listas, columnas, índices, validaciones y vistas lo hace un propietario del sitio, no TI.
- **Una sola lista regional** con `PaisCodigo`, en lugar de una por país. Así la app, los flujos y el modelo de Power BI son únicos para los 6 países.
- **Grupos del sitio:**

  | Grupo | Permiso |
  |---|---|
  | `Averías - Reportantes` | Colaborar |
  | `Averías - Aprobadores` | Colaborar |
  | `Averías - Control Inventarios` | Colaborar |
  | `Averías - Admin` (Logística regional) | Control total |

- **Catálogos y configuración:** solo los editan `Admin` y `Control Inventarios`. Para eso se rompe la herencia de permisos **de la lista**, no de cada ítem.
- **Limitación aceptada:** sin romper permisos por ítem, un usuario que entre directo a la lista ve los ítems de otros países. La app filtra por país y Power BI aplica RLS. Los permisos por ítem no compensan su costo operativo y degradan la lista a partir de unos miles de ítems.

## Modelo: 1 evento, N líneas [D8]

La política habla de "caso o lote consolidado" [7.3.1], por eso el ticket se divide en dos listas:

- **`Averias`** (encabezado): un evento de avería en una ubicación, con su clasificación, su evidencia, el flujo de aprobación y la disposición.
- **`Averias_Lineas`**: un SKU por línea, con su serie, cantidad, proveedor y valorización.

Las líneas alimentan al encabezado:

- **Costo del caso:** suma de las líneas.
- **Costo unitario de referencia para la matriz:** el **máximo** costo unitario entre las líneas [D3].

Las fotos y videos van en el encabezado: una foto muestra varias unidades y no se repite en cada línea.

---

## Lista `Averias` (encabezado)

"Lo llena" indica quién escribe el campo: **App** (Power Apps), **CI** (Control de Inventarios, en la app), **Flujo** (Power Automate) o **Sistema**.

### A. Identificación, ubicación y tiempos de reporte

| Nombre interno | Visible | Tipo | Oblig. | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `Title` | Folio | Una línea de texto | Sí | App (`PENDIENTE`) → Flujo | Formato `AV-{Pais}-{AAAA}-{ID con 6 dígitos}`. Indexado. |
| `PaisCodigo` | País | Elección: SV, GT, HN, NI, CR, P6 | Sí | App | Indexado. Es el filtro principal y el campo de RLS. |
| `Ubicacion` | Ubicación | Búsqueda → `Cat_Ubicacion` | Sí | App | Muestra el código, y el nombre y el tipo como campos adicionales. |
| `UbicacionCodigo` | Código ubicación | Una línea de texto | Sí | App | Copia del código, para delegación y para Power BI. Indexado. |
| `TipoUbicacion` | Tipo de ubicación | Elección: Tienda, CD, Bodega externa, 3PL, Última milla | Sí | App | Lo copia la app del catálogo. |
| `MatrizAplicable` | Matriz aplicable | Elección: Tienda, CD | Sí | App | [D7] Tienda y Última milla → **Tienda**. CD, Bodega externa y 3PL → **CD**. |
| `TiendaVendedoraCodigo` | Tienda vendedora | Una línea de texto | Solo si es Última milla | App | [D7] En última milla aprueba el gerente de la tienda que vendió. |
| `EtapaDeteccion` | Etapa de detección | Elección: Recepción de proveedor, Almacenamiento, Picking / despacho, Descarga en tienda, Exhibición / bodega de tienda, Entrega a cliente, Devolución de cliente | Sí | App | [5.1–5.4] |
| `FechaHoraDeteccion` | Fecha y hora de detección | **Fecha y hora** | Sí | App | [8.2.1] La hora es necesaria para medir el plazo de 24 h. |
| `FechaEnvio` | Fecha de reporte | Fecha y hora | No | Flujo | Primer envío. Es el inicio del SLA de aprobación. Indexado. |
| `HorasDeteccionAReporte` | Horas detección → reporte | Número, 1 decimal | No | Flujo | Es el KPI "Tiempo de reporte promedio" [9.2]. |
| `ReporteTardio` | Reporte tardío (> 24 h) | Sí/No | No | Flujo | `HorasDeteccionAReporte > MaxHorasDeteccionAReporte` (24). |
| `ReportanteEmail` | Correo del reportante | Una línea de texto | Sí | App (`User().Email`) | Se usa para la segregación y en Power BI. |

### B. Clasificación (obligatoria por política)

| Nombre interno | Visible | Tipo | Oblig. | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `TipoAveriaCodigo` | Tipo de avería | Una línea de texto (código de `Cat_TipoAveria`) | Sí | App | [4.1] Uno de los 6 tipos oficiales, el **desperfecto principal**. La app muestra un desplegable con el catálogo. |
| `Origen` | Origen / tipo de responsable | Elección: Proveedor local, Proveedor importado, Transporte propio, Transporte tercerizado, Centro de Distribución, Bodega externa, 3PL / operador logístico, Tienda, Entrega al cliente final | Sí | App → CI puede corregirlo en la valorización | [6.2] Los 9 tipos oficiales. Si el reportante no sabe si el proveedor es local o importado, CI lo corrige con Infor. |
| `CausaCodigo` | Causa | Una línea de texto (código de `Cat_Causa`) | Sí | App | Es la causa raíz. La app filtra las causas según el origen elegido. |
| `DescripcionDano` | Resumen del incidente | Varias líneas de texto | Sí | App | [8.2.2] Mínimo 15 caracteres, controlado en la app. |
| `Attachments` | Evidencia (fotos y videos) | Sistema | Sí, al menos 1 | App | [8.2.2] La app exige `FotosMinimas` según el tipo. |
| `Consolidado` | Consolidado en ubicación de averías | Sí/No | Sí para aprobar | App | [3, 5.4.5] Es el KPI "% inventario averiado consolidado". |
| `FechaConsolidacion` | Fecha de consolidación | Fecha y hora | No | App | |
| `UbicacionAveriasInfor` | Ubicación física de averías | Una línea de texto | No | App | Ubicación o almacén de averías en Infor o el WMS. |

### C. Valorización (totales a partir de las líneas)

| Nombre interno | Visible | Tipo | Oblig. | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `Moneda` | Moneda | Elección: USD, GTQ, HNL, NIO, CRC | Sí | App | Viene de la ubicación. |
| `TipoCambioAplicado` | Tipo de cambio aplicado | Número, 6 decimales | No | Flujo | Del período vigente en `Cfg_TipoCambio`. |
| `CostoTotalUSD` | Costo del caso USD | Número, 2 decimales | No | Flujo | Σ líneas, a **costo de adquisición** [7.3.1]. Indexado. |
| `CostoUnitarioMaxUSD` | Costo unitario máximo USD | Número, 2 decimales | No | Flujo | [D3] Es la base de la matriz. |
| `RetailTotalUSD` | Valor retail del caso USD | Número, 2 decimales | No | Flujo | Para los KPIs en retail [9] y el cobro a transportistas [5.2.1.4]. |
| `MontoFacturableUSD` | Monto facturable a terceros USD | Número, 2 decimales | No | Flujo / Finanzas | Retail si el origen es Transporte tercerizado, Bodega externa o 3PL. Si el origen es un proveedor, lo que diga el acuerdo comercial (lo carga Compras). Cero en los demás casos. |
| `MontoRecuperadoUSD` | Monto recuperado USD | Número, 2 decimales | No | Finanzas / Compras | Se puede actualizar después del cierre. |
| `ValorizadorEmail` | Valorizado por | Una línea de texto | No | Flujo | Para la segregación: quien valoriza no aprueba. |
| `FechaValorizacion` | Fecha de valorización | Fecha y hora | No | Flujo | |

### D. Aprobación

| Nombre interno | Visible | Tipo | Oblig. | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `Estado` | Estado | Elección (ver la máquina de estados) | Sí, predeterminado `Borrador` | App / Flujo | Indexado. |
| `NivelAprobacion` | Nivel | Elección: N1, N2, N3 | No | Flujo | [7.3] |
| `MotivoNivel` | Motivo del nivel | Elección múltiple: Costo unitario, Caso > 3 000, Recurrencia SKU, Recurrencia proveedor, Recurrencia tienda (frecuencia), Recurrencia tienda (monto) | No | Flujo | Explica al aprobador **por qué** le llegó el caso. |
| `RecurrenciaObservada` | Recurrencia (modo observación) | Sí/No | No | Flujo | Se marca durante el piloto en modo `Observar`, sin cambiar el nivel. |
| `RolAprobador` | Rol aprobador | Una línea de texto | No | Flujo | Gerente de Tienda, Operaciones local, Control de Inventarios o Gerente de Logística CD. |
| `Aprobador` | Aprobador | Persona | No | Flujo | Quien efectivamente respondió (puede ser el suplente). |
| `FechaAprobacion` | Fecha de aprobación o rechazo | Fecha y hora | No | Flujo | |
| `VersionMatriz` | Versión de matriz | Una línea de texto | No | Flujo | Se congela al enrutar. |
| `MotivoRechazo` | Motivo de rechazo o devolución | Varias líneas de texto | No | Flujo | |
| `AsignadoAEmail` | Asignado a | Una línea de texto | No | Flujo | A quién le toca el paso pendiente. Alimenta la bandeja "Mis pendientes" de la app (ver 06). **Indexado.** |
| `AsignadoRol` | Rol asignado | Una línea de texto | No | Flujo | |
| `AsignadoDesde` | Asignado desde | Fecha y hora | No | Flujo | Para la antigüedad y el semáforo de SLA en la app. |
| `Comentarios` | Bitácora del ticket | Varias líneas de texto, con **anexar cambios** activado | No | Flujo / App | [8.2.5] **Toda** comunicación del caso va acá: nada por correo ni por chat. |

### E. Diagnóstico y disposición

| Nombre interno | Visible | Tipo | Oblig. | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `DisposicionPropuesta` | Disposición propuesta | Elección: Reincorporación (reparación ST), Venta con descuento (outlet / remate), Devolución a proveedor local, Devolución a proveedor internacional, Destrucción, Donación | Sí | App (reportante) → Gerente responsable | [7.4–7.8] Es la disposición **física**. |
| `Recuperacion` | Vía de recuperación | Elección múltiple: Ninguna, Cobro a transportista / OPL (retail), Nota de crédito / compensación del proveedor, Reclamo a aseguradora | Sí | App / Gerente responsable | [5.2.1.4, 7.7, 3-#7] Va separada de la disposición física: un televisor dañado por el transporte se vende en outlet **y además** se le cobra al transportista. |
| `RequiereDiagnosticoST` | Requiere diagnóstico ST | Sí/No | No | Flujo | Sí cuando el tipo es Falla técnica o la disposición es Reincorporación [7.2.1, 7.5]. |
| `DiagnosticoST` | Diagnóstico ST | Elección: Reparable, No reparable, Sin falla (apto para venta), Garantía de proveedor | No | ST / Logística | |
| `NumeroInformeST` | N.º de informe ST | Una línea de texto | Si hay diagnóstico | ST / Logística | |
| `FechaDiagnosticoST` | Fecha de diagnóstico ST | Fecha y hora | No | Flujo | |
| `DescuentoAutorizadoPct` | % de descuento autorizado | Número, 0 decimales | Si es venta con descuento | Gerente de Producto (app) | [7.6] |
| `AutorizadorDisposicion` | Autorizó la disposición | Persona | No | Flujo | Gerente de Producto, CI o Compras, según la disposición. |
| `FechaAutorizacionDisposicion` | Fecha de autorización de la disposición | Fecha y hora | No | Flujo | |

### F. Ejecución y cierre

| Nombre interno | Visible | Tipo | Oblig. | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `NumeroAjusteInfor` | N.º de movimiento Infor | Una línea de texto | **Para cerrar** | CI | Ajuste, traslado a outlet o ST, o salida por RTV. **Power Apps no ajusta inventario: solo guarda el número.** Indexado. |
| `EvidenciaDisposicion` | Evidencia de la disposición | Una línea de texto | **Para cerrar** | CI / Logística | Acta de destrucción o donación [7.8.2], guía de RTV, factura de outlet o comprobante de reincorporación. |
| `NumeroNotaCredito` | N.º de nota de crédito / reclamo | Una línea de texto | No | Compras / Finanzas | No bloquea el cierre: la recuperación se mide aparte. |
| `FechaLimiteCierre` | Fecha límite de cierre | Fecha y hora | No | Flujo | `FechaHoraDeteccion + SLACierreDias` según el nivel. Se congela. |
| `FechaCierre` | Fecha de cierre (disposición final) | Fecha y hora | No | Flujo | |
| `DiasResolucionE2E` | Días de resolución E2E | Número, 1 decimal | No | Flujo | [9.1] Desde la detección hasta la disposición final. |
| `CerradoATiempo` | Cerrado a tiempo | Sí/No | No | Flujo | |

### Máquina de estados

```
Borrador ─(app)─► Enviado ─(AV-01)─► Pendiente valorización ─(CI valoriza líneas)─► Valorizado
Valorizado ─(AV-02: nivel y recurrencia)─► Pendiente aprobación
Pendiente aprobación ─rechaza─► Rechazado (fin)
Pendiente aprobación ─devuelve─► Devuelto para corrección ─(reportante corrige y reenvía)─► Enviado
Pendiente aprobación ─aprueba─► Pendiente diagnóstico ST   (si RequiereDiagnosticoST)
                              └► Pendiente disposición      (si no)
Pendiente diagnóstico ST ─(ST registra el diagnóstico)─► Pendiente disposición
Pendiente disposición ─(el gerente confirma la disposición)─► Disposición propuesta
Disposición propuesta ─(AV-03)─► Pendiente autorización disposición
   ─autoriza─► Pendiente ejecución
   ─rechaza─► Pendiente disposición (con motivo)
Pendiente ejecución ─(CI carga el N.º Infor y la evidencia)─► Cerrado (AV-04)
Borrador / Devuelto ─(reportante)─► Anulado (fin)
```

Valores de `Estado`: Borrador, Enviado, Pendiente valorización, Valorizado, Pendiente aprobación, Devuelto para corrección, Rechazado, Pendiente diagnóstico ST, Pendiente disposición, Disposición propuesta, Pendiente autorización disposición, Pendiente ejecución, Cerrado, Anulado.

**Por qué la valorización va antes de la aprobación:** la matriz [7.3] depende del costo unitario, y el aprobador **cambia** según el nivel (Gerente de Tienda, Operaciones o CI). Sin el costo no se sabe a quién mandar el caso. El costo sale de Infor y lo carga CI, nunca el reportante. **Segregación:** el analista de CI que valoriza no puede ser el aprobador de nivel 3, y el flujo lo controla.

---

## Lista `Averias_Lineas`

| Nombre interno | Visible | Tipo | Oblig. | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `Title` | Folio | Una línea de texto | Sí | App / Flujo | El mismo folio del encabezado. |
| `AveriaID` | ID de avería | Número, 0 decimales | Sí | App | ID del encabezado. **Indexado.** |
| `PaisCodigo` | País | Una línea de texto | Sí | App | Indexado, para la recurrencia. |
| `UbicacionCodigo` | Código ubicación | Una línea de texto | Sí | App | |
| `SKU` | SKU | Una línea de texto | Sí | App (escáner) | Validación: `=AND(LEN([SKU])>=4,LEN([SKU])<=20)`. **Indexado.** |
| `DescripcionProducto` | Producto | Una línea de texto | Sí | App | |
| `NumeroSerie` | N.º de serie | Una línea de texto | Sí | App | [8.2.2, D4] Obligatorio. Se permite `SIN SERIE` solo si se marca `SinSerie`. |
| `SinSerie` | Producto sin serie | Sí/No | No | App → CI lo verifica | [D4] CI confirma con Infor en la valorización que el SKU no se maneja con serie. |
| `Cantidad` | Cantidad | Número, 0 decimales | Sí | App | `=AND([Cantidad]>0,[Cantidad]<=9999)` |
| `SubtipoCodigo` | Subtipo | Una línea de texto (código de `Cat_Subtipo`) | No | App | Detalle para el análisis de causa raíz. |
| `Proveedor` | Proveedor | Una línea de texto | Para valorizar | CI | Desde Infor. **Indexado** (R2). |
| `CostoUnitarioLocal` | Costo unitario (local) | Número, 2 decimales | Para valorizar | CI | Costo de **adquisición** de Infor. |
| `PrecioRetailUnitarioLocal` | Precio retail unitario (local) | Número, 2 decimales | Para valorizar | CI | Precio de venta vigente. |
| `CostoUnitarioUSD` | Costo unitario USD | Número, 2 decimales | No | Flujo | |
| `CostoLineaUSD` | Costo de la línea USD | Número, 2 decimales | No | Flujo | |
| `RetailLineaUSD` | Retail de la línea USD | Número, 2 decimales | No | Flujo | |
| `OrigenImputable` | Origen del caso | Una línea de texto | No | Flujo | Copia del `Origen` del encabezado, para que las consultas de recurrencia no tengan que cruzar listas. |
| `EstadoCaso` | Estado del caso | Una línea de texto | No | Flujo | Copia de `Estado`; se excluyen los rechazados y anulados de la recurrencia. |
| `FechaEnvio` | Fecha de reporte | Fecha y hora | No | Flujo | **Indexado.** |

**Power Apps:** el formulario de reporte arma una colección de líneas y al enviar hace `Patch` del encabezado y luego `ForAll(colLineas, Patch(Averias_Lineas, …))`. Si falla alguna línea, el encabezado queda en `Borrador` y la app muestra el error. El encabezado pasa a `Enviado` **solo** cuando todas las líneas están guardadas, para que AV-01 no arranque con un caso incompleto.

---

## Validación de lista (`Averias`)

Va en una sola línea. Los saltos de abajo son solo para leerla:

```
=AND(
  [FechaHoraDeteccion]<=NOW(),
  OR([Estado]<>"Cerrado", AND(NOT(ISBLANK([NumeroAjusteInfor])), NOT(ISBLANK([EvidenciaDisposicion])))),
  OR([TipoUbicacion]<>"Última milla", NOT(ISBLANK([TiendaVendedoraCodigo])))
)
```

Mensaje: `Revisá: la detección no puede ser futura; para cerrar se necesitan el N.º de movimiento Infor y la evidencia; en última milla indicá la tienda vendedora.`

> Antes de producción hay que probar en el tenant que la validación acepte `NOW()`. Si no lo acepta, esa condición pasa a la app.

## Validaciones en Power Apps

- Al menos 1 línea. Fotos ≥ `FotosMinimas` del tipo de avería.
- `NumeroSerie` obligatorio en cada línea, salvo que tenga `SinSerie = Sí` con el valor `SIN SERIE` [D4].
- Coherencia entre ubicación y etapa: Tienda → Descarga en tienda, Exhibición / bodega de tienda o Devolución de cliente. CD, Bodega externa y 3PL → Recepción de proveedor, Almacenamiento o Picking / despacho. Última milla → Entrega a cliente.
- `Causa` filtrada por `Origen` (en `Cat_Causa`, columna `Origenes`).
- Aviso de posible duplicado: el mismo SKU en la misma ubicación en las últimas 72 h.
- **Aviso de plazo:** si pasaron más de 20 h desde la detección, la app muestra "Quedan X h para el plazo de 24 h de la política".
- No se puede aprobar si `Consolidado = No`. La app lo pide en la pantalla de aprobación.

## Índices

Hay que crearlos **antes** de llegar a 5 000 ítems.

| Lista | Columnas indexadas |
|---|---|
| `Averias` | `PaisCodigo`, `Estado`, `UbicacionCodigo`, `FechaEnvio`, `Title`, `NumeroAjusteInfor`, `AsignadoAEmail`, `ReportanteEmail`, `Created` |
| `Averias_Lineas` | `AveriaID`, `PaisCodigo`, `SKU`, `Proveedor`, `FechaEnvio` |

---

## Listas de soporte

Se crean con **Nueva lista → Desde CSV** y después se ajustan los tipos: SharePoint importa todo como texto.

| Lista | Archivo | Columnas clave | Mantiene |
|---|---|---|---|
| `Cat_TipoAveria` | `catalogos/tipo_averia.csv` | `Title`=Codigo; Nombre; Definicion; FotosMinimas (número); RequiereDiagnosticoST (Sí/No); Activo | Logística regional (es la clasificación oficial [4.1]: cambiarla requiere cambiar la política) |
| `Cat_Subtipo` | `catalogos/subtipo.csv` | `Title`=Codigo; Nombre; TipoAveriaCodigo; DisposicionSugerida; Activo | Logística regional |
| `Cat_Causa` | `catalogos/causa.csv` | `Title`=Codigo; Nombre; Origenes (texto con los orígenes separados por `;`); EtapaTipica; RecuperacionSugerida; Activo | Logística regional |
| `Cat_Ubicacion` | `catalogos/ubicacion.csv` | `Title`=Codigo (indexado); Nombre; Tipo; PaisCodigo (indexado); CDAbastecedor; CodigoInfor; Moneda; **FactorTamano** (número); **KRecurrenciaTienda** (número); Activo; EsEjemplo | CI de cada país; FactorTamano y KRecurrencia, cada trimestre |
| `Cfg_Matriz` | `config/matriz_aprobacion.csv` | `Title`=Version; Matriz (Tienda/CD); Nivel; UnitarioDesdeUSD; UnitarioHastaUSD; RolAprobador; SLAAprobacionHoras; SLACierreDias; Fuente; VigenteDesde; VigenteHasta; Activo | Solo Logística regional |
| `Cfg_Parametros` | `config/parametros_generales.csv` | `Title`=Clave; Valor; Descripcion | Solo Logística regional |
| `Cfg_Aprobadores` | `config/aprobadores_plantilla.csv` | PaisCodigo; UbicacionCodigo (`*` = todas); Rol (elección); Aprobador (**Persona**); Suplente (**Persona**); Activo | Gerente de Logística de cada país |
| `Cfg_TipoCambio` | `config/tipo_cambio.csv` | `Title`=Periodo (AAAA-MM); Moneda; UnidadesPorUSD; Fuente; Activo | Finanzas país, mensual |
| `Cfg_TablaPoisson` | `config/tabla_poisson.csv` | `Title`=LambdaHasta (número); K_alfa_2_5; K_alfa_1_0 | Fija |
| `Cfg_AccesoBI` | `config/acceso_bi_plantilla.csv` | Email; PaisCodigo (`*` = todos) | Logística regional |
| `Averias_Historial` | (vacía) | `Title`=Folio; AveriaID (indexado); Accion (elección: Enviado, Comentario, Valorizado, Aprobado, Rechazado, Devuelto, Diagnóstico ST, Disposición propuesta, Disposición autorizada, Disposición rechazada, Recordatorio, Escalado a suplente, Cerrado, Anulado); Rol; Actor (Persona); FechaInicio y FechaFin; DuracionHoras; SLAHoras; Comentario | Solo la escriben los flujos |

**Columnas Persona en `Cfg_Aprobadores`:** al importar desde CSV, los correos quedan como texto. Creá a mano `Aprobador` y `Suplente` como columnas Persona y pegá los correos en la vista de cuadrícula.

**Maestro de tiendas:** reemplazá las filas de ejemplo de `ubicacion.csv` con el maestro de Infor. `FactorTamano` = ventas (o unidades vendidas) de la tienda en los últimos 3 meses ÷ el promedio de las tiendas del país, tomado del BI de ventas. `KRecurrenciaTienda` = `K_alfa_1_0` de `Cfg_TablaPoisson` para `LambdaPaisTienda30d × FactorTamano` (ver D2).
