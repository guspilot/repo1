# 05 — Especificación de los flujos de Power Automate

Alineado con **POL-CO-0031 v2.0**, con el esquema [`01`](01_esquema_lista.md) y con las reglas [`03`](03_reglas_aprobacion.md).

## Diseño general

Son cinco flujos de nube. Todos usan **conectores estándar** (SharePoint, Approvals y Microsoft Teams), así que no requieren premium, Dataverse, conectores personalizados ni cuentas de servicio: **no hace falta TI**.

| Flujo | Disparador | Qué hace |
|---|---|---|
| **AV-01 Envío** | `Estado = Enviado` | Asigna el folio, mide el tiempo de reporte y le pide a CI la valorización |
| **AV-02 Nivel y aprobación** | `Estado = Valorizado` | Convierte a USD, totaliza las líneas, aplica la recurrencia y la matriz, y corre la aprobación del nivel que corresponde |
| **AV-03 Disposición** | `Estado = Disposición propuesta` | Valida los requisitos, pide la autorización según la disposición y avisa a ST, Compras o Finanzas |
| **AV-04 Cierre** | `Estado = Pendiente ejecución`, con el N.º Infor y la evidencia cargados | Cierra el caso y calcula el E2E y el cumplimiento del SLA |
| **AV-05 Seguimiento diario** | Programado: lunes a sábado, 07:00 (UTC-6) | Envía resúmenes de los casos vencidos por paso y por país |

**Por qué hay un flujo por estado:** cada paso humano (valorizar, diagnosticar, proponer la disposición, ejecutar en Infor) se hace en Power Apps y puede tardar días. Un flujo largo que esperara cada cambio tendría que consultar la lista en un bucle, y eso es frágil. Con un flujo por estado, si alguien corrige un ítem el proceso retoma solo.

**Power Apps no llama a los flujos.** La app solo escribe `Estado` y los flujos se disparan desde SharePoint.

### Cumplimiento de 8.2.4–8.2.5 (todo dentro del workflow)

- Las **decisiones** se toman solo en Approvals (que guarda la respuesta en el flujo) o en las pantallas de Power Apps. Teams y el correo solo **notifican** y llevan el enlace al ticket.
- Cada respuesta, comentario y acción se escribe en `Comentarios` (con anexar cambios) y en `Averias_Historial`.
- **Cada notificación de Teams termina con:** "Las decisiones sobre esta avería se toman solo en el ticket. No respondas por este chat."

### Configuración común a los cinco flujos

- **Dueño:** la cuenta de Logística regional, con al menos un **copropietario**.
- **Condiciones del disparador:** cada flujo arranca solo en su estado, para evitar bucles.
- **Simultaneidad del disparador:** activada, con grado 10.
- **Doble disparo:** la primera acción es *Obtener elemento*; si el `Estado` ya no es el esperado, el flujo hace *Terminar*.
- **Errores:** el cuerpo va en un ámbito `Try`. Un ámbito `Catch` (configurado para ejecutarse si `Try` falló o se agotó el tiempo) publica en Teams al grupo Admin el folio y este enlace a la ejecución:
  ```
  concat('https://make.powerautomate.com/environments/', workflow()?['tags']?['environmentName'], '/flows/', workflow()?['name'], '/runs/', workflow()?['run']?['name'])
  ```
- **Parámetros:** *Obtener elementos* de `Cfg_Parametros` y *Seleccionar* para armar el objeto. En este documento, `param('X')` es esa lectura.
- **Resolución de aprobadores (`ResolverRol(rol, ubicación)`):** en `Cfg_Aprobadores` con `Rol = rol` y `Activo = 1`, se busca en este orden:
  1. País + ubicación exacta.
  2. País + `*`.
  3. `*` + `*`.

  Se devuelven el aprobador y el suplente.
- **Segregación (`AplicarSegregacion(aprobador, excluidos)`):** si el aprobador está en la lista de excluidos, se usa el suplente. Si el suplente también está, se avisa al Gerente de Logística del país y se usa el suplente de `Control de Inventarios - Aprobador`.
- **Esperar con recordatorio y escalamiento (`EsperarConEscalamiento`):**
  1. *Crear una aprobación* y *Esperar una aprobación* con un tiempo de espera de `PT{HorasRecordatorio}H`.
  2. Si se agota: recordatorio por Teams, registro en el historial y segunda espera hasta `HorasEscalamientoSuplente`.
  3. Si se agota otra vez: se crea la aprobación al suplente con el título `[ESCALADA]`, se avisa al aprobador original que su respuesta ya no cuenta, se registra en el historial y se espera hasta `P20D`.
  4. Después de **cada** espera que termine bien, *Establecer variable* `varResp`.

  No se usa `coalesce(body(...))` porque referenciar una acción omitida hace fallar el flujo.
- **Rechazo o devolución sin comentario:** no se acepta. Se vuelve a crear la aprobación con el aviso "Rechazar o devolver requiere comentario", porque Approvals no permite exigir el comentario.
- **Zona horaria:** las fechas se guardan en UTC. Para el folio y el período de tipo de cambio se usa `convertFromUtc(utcNow(), 'Central America Standard Time', ...)`.
- **Enlace a la app:** `https://apps.powerapps.com/play/<AppId>?id=<ID>`.

### Límites de solicitudes

Con licencia M365, el límite es del orden de **6 000 solicitudes cada 24 h por usuario dueño**; verificá el valor vigente. Un caso completo usa ~60–90 acciones entre los cinco flujos, contando la recurrencia por línea.

| Volumen del país | Casos/día | Acciones/día | ¿Entra con un solo dueño? |
|---|---|---|---|
| Base (≈ 258 casos/mes) | ~12 | ~900 | Sí |
| Alto (≈ 505 casos/mes) | ~23 | ~1 800 | Sí |
| **6 países, volumen alto** | ~140 | ~10 800 | **No** |

**A escala regional hace falta repartir.** Recomiendo que AV-02 (el más pesado) quede a nombre de un dueño distinto de los demás flujos, o duplicar AV-02 por grupo de países con dueños distintos. El límite es por usuario.

---

## AV-01 — Envío

**Disparador:** *Cuando se crea o modifica un elemento* en `Averias`.

**Condición del disparador:** `@equals(triggerOutputs()?['body/Estado/Value'], 'Enviado')`

| # | Acción | Detalle |
|---|---|---|
| 1 | Obtener elemento y verificar el estado | |
| 2 | Obtener elementos de `Averias_Lineas` con `AveriaID eq {ID}` | Si no hay ninguna línea: `Estado = Borrador`, aviso por Teams al reportante y *Terminar*. |
| 3 | Componer el folio | Si `Title = 'PENDIENTE'`: `concat('AV-', PaisCodigo, '-', yyyy, '-', formatNumber(ID,'000000'))`. Si no, se conserva (es un reenvío). |
| 4 | Componer `FechaEnvio` | `if(empty(FechaEnvio), utcNow(), FechaEnvio)`. En un reenvío se conserva la fecha original. |
| 5 | Componer las horas de reporte | `div(sub(ticks(FechaEnvio), ticks(FechaHoraDeteccion)), 36000000000.0)`. `ReporteTardio = greater(horas, float(param('MaxHorasDeteccionAReporte')))`. |
| 6 | Actualizar elemento | `Title`, `FechaEnvio`, `HorasDeteccionAReporte`, `ReporteTardio` y `Estado = Pendiente valorización`. En `Comentarios` se anexa "Reportado por {ReportanteEmail}". |
| 7 | *Aplicar a cada uno* sobre las líneas → Actualizar elemento | En cada línea: `Title = folio`, `FechaEnvio` y `EstadoCaso = Pendiente valorización`. |
| 8 | Historial | `Accion = Enviado`. |
| 9 | `ResolverRol('Control de Inventarios - Valorizador', ubicación)` | |
| 10 | Teams al valorizador | "Valorizar {Folio}: {n} líneas en {UbicacionCodigo}. SLA {SLAValorizacionHoras} h", con el enlace a la pantalla **Valorizar**. Si `ReporteTardio`, se agrega "⚠ Reportado {h} h después de la detección (política: 24 h)". |

**Pantalla Valorizar (Power Apps, para CI):** por cada línea se cargan proveedor, costo unitario y precio retail desde Infor, y se verifica `SinSerie`. En el encabezado CI puede corregir el `Origen` (proveedor local o importado) y la `CausaCodigo`. Al guardar: `Estado = Valorizado` y `ValorizadorEmail = User().Email`. La app no deja guardar si falta algún costo o algún retail.

---

## AV-02 — Nivel y aprobación de la avería

**Disparador:** *Cuando se crea o modifica un elemento* en `Averias`, con la condición `@equals(triggerOutputs()?['body/Estado/Value'], 'Valorizado')`.

### A. Valorización en USD

| # | Acción | Detalle |
|---|---|---|
| 1 | Obtener elemento y verificar el estado; leer los parámetros | |
| 2 | Tipo de cambio | De `Cfg_TipoCambio` para el mes actual y la `Moneda`. Si falta, se usa el del mes anterior y se avisa al Admin. Si tampoco está, aviso y *Terminar*: el caso queda en `Valorizado` y se reprocesa cuando se cargue el TC. |
| 3 | Obtener las líneas | |
| 4 | *Aplicar a cada uno* línea → Actualizar elemento de la línea | `CostoUnitarioUSD = div(CostoUnitarioLocal, TC)`, `CostoLineaUSD = mul(Cantidad, CostoUnitarioUSD)`, `RetailLineaUSD = div(mul(Cantidad, PrecioRetailUnitarioLocal), TC)`, `OrigenImputable = Origen` del encabezado, y `EstadoCaso = Valorizado`. Todo redondeado a 2 decimales. Las variables `varCosto`, `varRetail` (Float, se incrementan) y `varUnitMax` (`max()`) se van actualizando. |
| 5 | Componer `MontoFacturable` | Si `Origen` está en {Transporte tercerizado, Bodega externa, 3PL / operador logístico}: `varRetail` [5.2.1.4]. En otro caso: 0. Para los proveedores lo carga Compras. |

### B. Recurrencia (D2, V3)

Se cuentan casos distintos del mismo país, sin incluir `EstadoCaso` en {Rechazado, Anulado, Borrador}.

| # | Regla | Acciones |
|---|---|---|
| 6 | **R1, SKU** (por cada línea, solo si `Origen` es Proveedor local o importado) | *Obtener elementos* de `Averias_Lineas` con `PaisCodigo eq '{p}' and SKU eq '{sku}' and FechaEnvio ge '{hoy − RecHistoriaDias}'`. Con *Filtrar matriz*: `OrigenImputable` de proveedor y estado válido. Se separan dos grupos: **ventana** (últimos `RecSKU_VentanaDias`) e **historia** (de −240 a −60 días). `nVentana` = cantidad de `AveriaID` distintos en la ventana: `length(union(...))` sobre un *Seleccionar* de `AveriaID`. `λ = nHistoria / 180 × 60`. `k` = `K_alfa_2_5` de la primera fila de `Cfg_TablaPoisson` con `LambdaHasta ≥ λ`. **R1 se cumple si `nVentana ≥ max(RecSKU_Piso, k)`.** |
| 7 | **R2, proveedor** (por cada proveedor distinto de las líneas, con la misma condición de origen) | Igual que R1, filtrando por `Proveedor eq '{prov}'` y con `RecProv_Piso` y `RecProv_VentanaDias`. |
| 8 | **R3a y R3b, tienda** (solo para la matriz Tienda; en última milla se usa la tienda vendedora) | *Obtener elementos* de `Averias` con `UbicacionCodigo eq '{u}' and FechaEnvio ge '{hoy − RecTienda_VentanaDias}'`, filtrando los estados válidos. `n` = conteo, incluido el caso actual. `usd` = suma de `CostoTotalUSD` (con *Aplicar a cada uno* e *Incrementar variable*) + `varCosto`. Con `FactorTamano` y `KRecurrenciaTienda` de `Cat_Ubicacion`: **R3a = `n ≥ KRecurrenciaTienda`**; **R3b = `n ≥ RecTienda_MinCasosMonto` y `usd ≥ RecTienda_MontoUSD × max(1, FactorTamano)`**. |
| 9 | Componer `Recurrente` | `or(R1, R2, R3a, R3b)` y los motivos. Si `param('RecurrenciaModo') = 'Observar'`: `RecurrenciaObservada = Recurrente` y, **para el nivel**, `Recurrente = false`. |

### C. Nivel y aprobador

| # | Acción | Detalle |
|---|---|---|
| 10 | Obtener `Cfg_Matriz` con `Activo eq 1`, filtrado por `Matriz = MatrizAplicable` y vigencia | |
| 11 | Componer `NivelUnit` | La fila con `UnitarioDesdeUSD ≤ varUnitMax ≤ UnitarioHastaUSD`. |
| 12 | Componer el nivel final | Si `Recurrente` o `varCosto > CasoMaxSinNivel3USD`, va a la fila **N3** de la matriz. Si no, se queda en `NivelUnit`. Se arma `MotivoNivel`: Costo unitario, Caso > 3 000 y/o los motivos de recurrencia. |
| 13 | Aprobador | `ResolverRol(fila.RolAprobador, ubicación o tienda vendedora)`, luego `AplicarSegregacion` excluyendo a `ReportanteEmail` y, si el nivel es N3, también a `ValorizadorEmail`. |
| 14 | Actualizar elemento | `TipoCambioAplicado`, `CostoTotalUSD = varCosto`, `CostoUnitarioMaxUSD = varUnitMax`, `RetailTotalUSD = varRetail`, `MontoFacturableUSD`, `FechaValorizacion`, `NivelAprobacion`, `MotivoNivel`, `RecurrenciaObservada`, `RolAprobador`, `VersionMatriz`, `RequiereDiagnosticoST`, `FechaLimiteCierre = addDays(FechaHoraDeteccion, fila.SLACierreDias)` y `Estado = Pendiente aprobación`. `RequiereDiagnosticoST` = TP5, o tipo con `RequiereDiagnosticoST = Sí`, o disposición = Reincorporación. |
| 15 | Historial | `Accion = Valorizado`, `Actor = valorizador`, duración desde `FechaEnvio` y `SLAHoras = SLAValorizacionHoras`. |
| 16 | D6 | Si `MatrizAplicable = CD` y `varCosto > NotificarRegionalCasoUSD`: Teams **informativo** al Gerente de Logística regional. |

### D. Aprobación

| # | Acción | Detalle |
|---|---|---|
| 17 | `EsperarConEscalamiento` | Respuestas personalizadas: `Aprobar`, `Rechazar`, `Devolver para corrección`. Título: `Avería {Folio} · {Nivel} · USD {CostoTotalUSD} · {UbicacionCodigo}`. Los detalles incluyen tipo, origen, causa, resumen, líneas (SKU × cantidad × costo unitario USD), cantidad de fotos, horas de reporte y `MotivoNivel`. Si hay recurrencia, se destaca en negrita, por ejemplo "⚠ Recurrencia de tienda: {n} casos / USD {usd} en 30 días". |
| 18 | **Switch** según la respuesta | |
| 18a | `Aprobar` | Actualizar elemento: `Aprobador`, `FechaAprobacion`, se anexa a `Comentarios`, y `Estado` = `Pendiente diagnóstico ST` si `RequiereDiagnosticoST`, o `Pendiente disposición` si no. En las líneas, `EstadoCaso = Aprobado`. Historial con la duración y `SLAHoras = 48`. Si va a ST: Teams a `Servicio Técnico (ST)` con el folio, las líneas y el enlace a la pantalla **Diagnóstico**. Si no: Teams al Gerente de Tienda o de Logística del CD con el enlace a la pantalla **Disposición**. |
| 18b | `Rechazar` | `Estado = Rechazado` y `MotivoRechazo`. En las líneas, `EstadoCaso = Rechazado`. Teams al reportante. |
| 18c | `Devolver` | `Estado = Devuelto para corrección` y `MotivoRechazo`. Teams al reportante. Al reenviar, el caso vuelve a valorizarse, porque las líneas pueden haber cambiado. |

> **Validación previa en la app:** la pantalla de aprobación no muestra el botón Aprobar si `Consolidado = No` [3, 5.4.5]. Si se aprueba desde Teams u Outlook, el flujo lo vuelve a validar en 18a: si `Consolidado = No`, cambia el resultado a `Devolver` con el motivo "Consolidar el producto antes de aprobar".

**Pantalla Diagnóstico (ST o Logística):** se cargan `DiagnosticoST` y `NumeroInformeST`. Al guardar, `Estado = Pendiente disposición`. Si el diagnóstico es `No reparable`, la app quita Reincorporación de las opciones.

**Pantalla Disposición (Gerente de Tienda o de Logística del CD):** confirma o cambia `DisposicionPropuesta` y `Recuperacion` y pasa el caso a `Estado = Disposición propuesta`.

---

## AV-03 — Autorización de la disposición

**Disparador:** `@equals(triggerOutputs()?['body/Estado/Value'], 'Disposición propuesta')`

| # | Acción | Detalle |
|---|---|---|
| 1 | Obtener elemento y verificar el estado | |
| 2 | Validar los requisitos | **Reincorporación** requiere `DiagnosticoST` en {Reparable, Sin falla}. **Devolución a proveedor local o internacional** requiere `Origen` = Proveedor local o importado según corresponda [7.7.1]. **Destrucción o donación** requiere `DiagnosticoST ≠ Reparable` si hubo diagnóstico. Si algo falla: `Estado = Pendiente disposición`, se anexa el motivo a `Comentarios`, Teams al gerente y *Terminar*. |
| 3 | Actualizar elemento | `Estado = Pendiente autorización disposición`. |
| 4 | **Switch** según `DisposicionPropuesta` | |
| 4a | Reincorporación | No hay autorización adicional [7.5]: se pasa directo a `Estado = Pendiente ejecución`. Teams a Logística para el traslado a ST con el comprobante de movimiento [7.5.2]. |
| 4b | Venta con descuento | Teams al **Gerente de Producto** (`ResolverRol('Gerente de Producto', país)`) con el enlace a la pantalla **Autorizar descuento**, donde carga `DescuentoAutorizadoPct` y elige Autorizar o Rechazar. *Hacer hasta* que el estado cambie (consulta cada 4 h, tiempo de espera `PT{SLAAutorizacionDescuentoHoras}H`). Si vence: recordatorio y escalamiento al suplente. **Es el único paso con espera por consulta:** Approvals no captura números y el % es obligatorio. |
| 4c | Devolución a proveedor local o internacional | `EsperarConEscalamiento` a **Compras** con las opciones `Procede` / `No procede`. Si es internacional, Teams **informativo** a Finanzas y Seguros por la provisión [7.7.3.1]. |
| 4d | Destrucción o donación | `EsperarConEscalamiento` a **`Control de Inventarios - Aprobador`** con las opciones `Validar` / `No validar` [7.8.1]. En los detalles: "Se requerirá acta formal, fotos y contrato si es donación [7.8.2]". |
| 5 | Resultado | **Autorizado:** `Estado = Pendiente ejecución`, `AutorizadorDisposicion`, `FechaAutorizacionDisposicion` e historial. **Rechazado:** `Estado = Pendiente disposición`, motivo anexado y Teams al gerente. |
| 6 | Recuperación (paralela, no bloquea) | Si `Recuperacion` incluye "Cobro a transportista / OPL" o "Reclamo a aseguradora": Teams a **Finanzas y Seguros** con `MontoFacturableUSD` (a retail) [5.2.1.4, 3-#7]. Si incluye "Nota de crédito / compensación del proveedor": Teams a **Compras**. |
| 7 | Aviso de ejecución | Teams a CI: "Ejecutar en Infor {Folio}: {disposición}. Motivo de movimiento sugerido: {tabla}. SLA {SLAEjecucionDias} días. Cargá el N.º de movimiento y la evidencia en la pantalla **Cerrar**". |

| Disposición | Movimiento Infor | Evidencia |
|---|---|---|
| Reincorporación | Traslado a la bodega de ST; reincorporación al activo después de la prueba | Comprobante digital de movimiento [7.5.2] |
| Venta con descuento | Traslado a la ubicación de outlet o remate | N.º de traslado |
| Devolución a proveedor local o internacional | Salida por RTV, o ajuste contra la provisión | Guía de RTV, o NC o compensación |
| Destrucción o donación | Ajuste por baja | **Acta** formal (y contrato si es donación) |

> Los **códigos de motivo de movimiento de Infor** de cada disposición los tiene que definir Control de Inventarios de cada país. Sin eso, la conciliación entre Infor y el workflow no va a cuadrar.

---

## AV-04 — Cierre

**Disparador** (en una sola línea):
```
@and(equals(triggerOutputs()?['body/Estado/Value'],'Pendiente ejecución'), not(empty(triggerOutputs()?['body/NumeroAjusteInfor'])), not(empty(triggerOutputs()?['body/EvidenciaDisposicion'])))
```

| # | Acción | Detalle |
|---|---|---|
| 1 | Obtener elemento y verificar el estado | |
| 2 | Validaciones | Si la disposición es destrucción o donación y no hay fotos adjuntas posteriores a `FechaAutorizacionDisposicion` (se verifica con *Obtener datos adjuntos*), se avisa a CI y no se cierra [7.8.2]. Si `NumeroAjusteInfor` ya existe en otro caso, solo se avisa, porque un mismo movimiento puede cubrir varios casos. |
| 3 | Actualizar elemento | `Estado = Cerrado`, `FechaCierre = utcNow()`, `DiasResolucionE2E = div(sub(ticks(utcNow()), ticks(FechaHoraDeteccion)), 864000000000.0)` y `CerradoATiempo = lessOrEquals(ticks(utcNow()), ticks(FechaLimiteCierre))`. En las líneas, `EstadoCaso = Cerrado`. |
| 4 | Historial | `Accion = Cerrado`, con la duración desde la autorización. |
| 5 | Teams al reportante y al gerente | "Avería {Folio} cerrada (Infor {N.º})". |

---

## AV-05 — Seguimiento diario

**Disparador:** periodicidad diaria a las 07:00 `(UTC-06:00) Central America`, de lunes a sábado.

Por cada estado abierto se hace una consulta (con la paginación activada) y se comparan las fechas contra su SLA:

| Estado | Vencido si… | A quién |
|---|---|---|
| Pendiente valorización | `FechaEnvio + SLAValorizacionHoras < ahora` | CI (valorizador) |
| Pendiente aprobación | Más de 48 h desde `FechaValorizacion` | Rol aprobador y Gerente de Logística del país (resumen) |
| Pendiente diagnóstico ST | `FechaAprobacion + SLADiagnosticoSTDias < ahora` | ST y Logística |
| Pendiente disposición | Más de 2 días desde la aprobación o el diagnóstico | Gerente de Tienda o del CD |
| Pendiente autorización disposición | Según el SLA de la disposición | Gerente de Producto, Compras o CI |
| Pendiente ejecución | `FechaAutorizacionDisposicion + SLAEjecucionDias < ahora` | CI |
| Cualquier estado abierto | `FechaLimiteCierre < ahora` | Gerente de Logística del país (resumen) |

Por país se arma una *Crear tabla HTML* y se manda por Teams. **Si no hay vencidos, no se manda nada.** Los umbrales acumulados y las alertas de concentración van como **alertas de datos de Power BI**, no en este flujo.

---

## Pruebas antes de producción

Se corren en una lista de prueba con los mismos nombres internos.

| # | Caso | Esperado |
|---|---|---|
| 1 | Tienda: 1 línea de USD 80 | N1, aprueba el Gerente de Tienda |
| 2 | Tienda: 1 línea de USD 100.00 | N1 (el límite está incluido) |
| 3 | Tienda: 1 línea de USD 350 | N2, aprueba Operaciones local |
| 4 | Tienda: 2 líneas, de USD 50 y USD 700 | N3 por el unitario máximo [D3] |
| 5 | Tienda: 40 unidades de USD 90 (USD 3 600) | N3 por caso > 3 000 [D1] |
| 6 | CD: 1 línea de USD 150 | N3, aprueba CI sin pasar por Operaciones |
| 7 | Bodega externa: USD 60 | Matriz CD, N1, aprueba el Gerente de Logística del CD [D7] |
| 8 | Última milla con tienda vendedora SV-T014 | Aprueba el gerente de SV-T014 |
| 9 | Tercer caso imputable al proveedor del mismo SKU en 60 días, con `Aplicar` | N3 con motivo "Recurrencia SKU" |
| 10 | El mismo caso, con `Observar` | Nivel por monto y `RecurrenciaObservada = Sí` |
| 11 | El valorizador de CI es también el aprobador de N3 | Va al suplente |
| 12 | Detección registrada 30 h antes del envío | `ReporteTardio = Sí` y aviso a CI |
| 13 | Aprobación sin `Consolidado` | Se devuelve con el motivo |
| 14 | Falla técnica (TP5) aprobada | Pasa por Pendiente diagnóstico ST |
| 15 | Diagnóstico No reparable y disposición Reincorporación | AV-03 lo devuelve a Pendiente disposición |
| 16 | Venta con descuento | El Gerente de Producto carga el % y la autoriza; si pasan 72 h, recordatorio y suplente |
| 17 | Destrucción | CI valida; no cierra sin fotos posteriores ni acta |
| 18 | Origen Transporte tercerizado | `MontoFacturableUSD = RetailTotalUSD` y aviso a Finanzas |
| 19 | Cierre después de `FechaLimiteCierre` | `CerradoATiempo = No` |
| 20 | Falta el TC del mes | Usa el del mes anterior y avisa al Admin |
