# 05 — Especificación de los flujos de Power Automate

## Diseño general

Son cuatro flujos de nube, todos con **conectores estándar**: SharePoint, Approvals, Microsoft Teams y Office 365 Outlook (solo de respaldo). No se usan conectores premium, Dataverse, conectores personalizados, registros de aplicación ni cuentas de servicio, así que no hace falta TI.

| Flujo | Disparador | Qué hace |
|---|---|---|
| **AV-01 Envío y N1** | La lista `Averías` pasa a `Estado = Enviado` | Asigna el folio, fija `FechaEnvio`, resuelve el jefe de la ubicación, pide la aprobación N1 y la pasa a valorización |
| **AV-02 Valorización y N2–N4** | La lista pasa a `Estado = Valorizado` | Convierte a USD, aplica el anti-fraccionamiento, calcula el tramo, corre N2–N4 y avisa a Control de Inventarios para el ajuste en Infor |
| **AV-03 Cierre** | `Estado = Pendiente ajuste Infor` con `NumeroAjusteInfor` y `EvidenciaDisposicion` cargados | Cierra el caso y calcula `CerradoATiempo` |
| **AV-04 Seguimiento diario** | Programado, de lunes a sábado a las 07:00 (UTC-6) | Envía por Teams resúmenes de valorizaciones y ajustes de Infor vencidos |

**Por qué hay flujos separados y no uno largo:** la valorización y el ajuste en Infor son trabajo humano que se hace en Power Apps y puede tardar días. Un flujo que espera un cambio en un ítem tendría que consultar la lista en un bucle, lo que gasta acciones y es frágil. Con un disparador por estado, cada flujo es corto y fácil de depurar, y si alguien corrige un ítem a mano en SharePoint, el proceso retoma solo.

**Power Apps no llama a los flujos directamente.** La app solo escribe `Estado` y los flujos se disparan desde SharePoint. Así se evitan los problemas de conexiones del disparador de Power Apps y el proceso funciona aunque alguien edite desde la lista.

### Configuración común a los cuatro flujos

- **Propiedad:** el dueño es la cuenta de Logística regional y hay al menos un **copropietario** (Compartir → agregar propietario). Si el único dueño se va de la empresa, los flujos se detienen.
- **Condiciones del disparador** (Configuración del disparador → Condiciones del desencadenador): cada flujo arranca solo en su estado. Esto evita bucles cuando el mismo flujo actualiza el ítem.
- **Control de simultaneidad del disparador:** activado, con grado 10. Evita picos de acciones a la misma hora.
- **Protección contra doble disparo:** la primera acción vuelve a leer el ítem con *Obtener elemento* y una condición termina el flujo si `Estado` ya no es el esperado. Una edición rápida puede generar dos eventos de modificado.
- **Manejo de errores:** el cuerpo va en un ámbito `Try`. Un ámbito `Catch` con *Configurar ejecución después de* = "ha fallado" o "ha agotado el tiempo de espera" publica en Teams, al grupo Admin, el folio y el enlace a la ejecución:
  ```
  concat('https://make.powerautomate.com/environments/', workflow()?['tags']?['environmentName'], '/flows/', workflow()?['name'], '/runs/', workflow()?['run']?['name'])
  ```
- **Lectura de parámetros:** cada flujo empieza con *Obtener elementos* de `Cfg_Parametros` y una acción *Seleccionar* que arma el objeto `{Clave: Valor}`. Después se lee, por ejemplo, `int(body('Param')?['HorasRecordatorio'])`. Las expresiones de abajo usan `param('X')` como abreviatura de eso.
- **Zona horaria:** SharePoint guarda las fechas en UTC. Para el folio y el período de tipo de cambio se usa `convertFromUtc(utcNow(), 'Central America Standard Time', 'yyyy-MM')`.
- **Enlaces:** cada notificación lleva el enlace al ítem y un enlace directo a la app: `https://apps.powerapps.com/play/<AppId>?id=<ID>`. La app lo lee con `Param("id")` en `StartScreen`.

### Límites de solicitudes: hay que dimensionarlos

Los flujos corren con las licencias del dueño. Con licencia Microsoft 365, el límite de Power Platform es del orden de **6 000 solicitudes cada 24 h por usuario**; conviene verificar el valor vigente en la documentación de Microsoft, porque cambia. Una avería completa consume ≈ 35–60 acciones entre los 4 flujos.

| Volumen | Averías por día | Acciones por día (≈ 50/caso) | Situación |
|---|---|---|---|
| Bajo (1 440/mes) | ~48 | ~2 400 | Holgado |
| Alto (2 760/mes) | ~92 | ~4 600 | Cerca del límite en días pico |

**Mitigación sin TI:** si el volumen real es alto, que cada flujo tenga un dueño distinto. Por ejemplo, AV-02, que es el más pesado, a nombre de otra persona de Logística regional. El límite es por usuario, así que eso lo multiplica. El indicador para vigilarlo está en Power Platform admin center → Análisis, si es accesible; si no, en el historial de ejecuciones, buscando estados "Limitado".

---

## AV-01 — Envío y aprobación N1

**Disparador:** SharePoint → *Cuando se crea o modifica un elemento* (sitio de Averías, lista `Averías`).

**Condición del disparador:**
```
@equals(triggerOutputs()?['body/Estado/Value'], 'Enviado')
```

| # | Acción | Detalle |
|---|---|---|
| 1 | Obtener elemento | Por ID del disparador. **Condición:** si `Estado ≠ Enviado`, *Terminar* (correcto). |
| 2 | Obtener elementos `Cfg_Parametros` + Seleccionar | Arma el objeto de parámetros. |
| 3 | Componer `Folio` | Si `Title = 'PENDIENTE'`: `concat('AV-', PaisCodigo, '-', convertFromUtc(utcNow(),'Central America Standard Time','yyyy'), '-', formatNumber(ID,'000000'))`; si no, conservar `Title` (es un reenvío). |
| 4 | Componer `FechaEnvio` | `if(empty(FechaEnvio), utcNow(), FechaEnvio)`. **En un reenvío tras devolución se conserva la fecha original**: el SLA corre desde la primera vez. Si no fuera así, devolver un caso reiniciaría el reloj. |
| 5 | Componer `ReporteTardio` | `greater(div(sub(ticks(FechaEnvio), ticks(FechaDeteccion)), 864000000000), int(param('MaxDiasDeteccionAReporte')))` |
| 6 | Obtener elementos `Cfg_Aprobadores` | Consulta de filtro: `PaisCodigo eq '{PaisCodigo}' and Rol eq 'Jefe de ubicación' and Activo eq 1`. |
| 7 | Filtrar matriz ×2 + Componer `Jefe` | Primero `UbicacionCodigo = {UbicacionCodigo}`; si queda vacío, `UbicacionCodigo = '*'`. Toma `first()`. **Si los dos quedan vacíos:** Teams al Admin con "Sin jefe configurado para {ubicación}", deja `Estado = Enviado` y termina (falló). |
| 8 | Segregación | Si `toLower(Jefe.Aprobador.Email) = toLower(ReportanteEmail)`, usa `Jefe.Suplente`. Si el suplente también es el reportante, avisa al Admin y termina. |
| 9 | Actualizar elemento | `Title = Folio`, `FechaEnvio`, `ReporteTardio`, `Estado = Pendiente N1`, `NivelActual = 1`, `JefeUbicacion = aprobador resuelto`. |
| 10 | Crear elemento `Averias_Historial` | `Accion = Enviado`, `Nivel = 0`, `Actor = Author`, `FechaInicio = FechaFin = utcNow()`. |
| 11 | Approvals → **Crear una aprobación** | Tipo: **Respuestas personalizadas: esperar una respuesta**. Opciones: `Aprobar`, `Rechazar`, `Devolver para corrección`. Título: `Avería {Folio} · {UbicacionCodigo} · {TipoAveria}`. Asignado a: el jefe resuelto. Detalles (Markdown): SKU, descripción, cantidad, etapa, causa, responsable imputable, descripción del daño, cantidad de fotos, fecha de detección y la advertencia de reporte tardío si aplica. Enlace del elemento: el enlace de la app. **Sin costo**: todavía no está valorizado. |
| 12 | Approvals → **Esperar una aprobación** (ID del paso 11) | **Configuración → Tiempo de espera:** `PT{HorasRecordatorio}H` (`PT24H`). |
| 13 | *Si 12 agotó el tiempo* (ejecutar después de "ha agotado el tiempo de espera") | Teams → *Publicar mensaje en un chat o canal* (como Flow bot, chat con el aprobador): "Tenés pendiente la avería {Folio} desde hace 24 h". Historial: `Accion = Recordatorio`. Luego **Esperar una aprobación** del mismo ID con tiempo de espera `PT{HorasEscalamientoSuplente − HorasRecordatorio}H` (`PT24H`). |
| 14 | *Si el segundo wait agotó el tiempo* | **Crear una aprobación** igual a la del paso 11, asignada al **suplente**, con el título prefijado `[ESCALADA]`. Avisa al aprobador original por Teams que el caso se reasignó y que su respuesta ya no cuenta. Historial: `Accion = Escalado a suplente`. **Esperar una aprobación** con tiempo de espera `P20D`. Si también vence: Teams al Gerente de logística país y al Admin, y termina. |
| 15 | Variable `varResp` (Object) | Inicializada vacía al principio del flujo. **Después de cada uno de los tres waits** que termine bien, *Establecer variable* `varResp = body('<ese wait>')`. No se usa `coalesce(body(...))` sobre los tres waits porque una expresión que referencia una acción omitida falla. De `varResp` salen `Resultado = outcome`, `Respondio = responses[0].responder.email` y `Comentario = responses[0].comments`. |
| 16 | **Switch** sobre `Resultado` | Ver abajo. |

**Rama `Aprobar`:**
1. Resuelve `Control de inventarios` con el mismo patrón de los pasos 6–7 (rol, país, `*`).
2. Actualizar elemento: `AprobadorN1 = Respondio`, `FechaN1 = utcNow()`, `Estado = Pendiente valorización`, `NivelActual = 0`, `ControlInventarios = resuelto`, `ComentarioAprobacion = 'N1: ' + Comentario`.
3. Historial: `Accion = Aprobado`, `Nivel = 1`, `FechaInicio = FechaEnvio` (o la fecha de reenvío), `FechaFin = utcNow()`, `DuracionHoras = div(sub(ticks(utcNow()), ticks(FechaInicio)), 36000000000.0)`.
4. Teams a Control de Inventarios: "Valorizar {Folio}: SKU {SKU} × {Cantidad} en {UbicacionCodigo} ({CodigoInfor}). SLA {SLAValorizacionHoras} h." más el enlace a la pantalla de valorización.

**Rama `Rechazar`:**
1. Actualizar elemento: `Estado = Rechazado`, `AprobadorN1`, `FechaN1`, `FechaAprobacionFinal = utcNow()`, `MotivoRechazo = Comentario`.
2. Historial: `Accion = Rechazado`, `Nivel = 1`.
3. Teams al reportante con el motivo.
4. **Si `Comentario` está vacío**, el flujo no rechaza: crea otra vez la aprobación con el texto "El rechazo requiere comentario". Las aprobaciones no permiten exigir el comentario, así que la regla se aplica acá.

**Rama `Devolver para corrección`:**
1. Actualizar elemento: `Estado = Devuelto para corrección`, `MotivoRechazo = Comentario`. `FechaEnvio` no se toca.
2. Historial: `Accion = Devuelto`, `Nivel = 1`.
3. Teams al reportante: "Corregí la avería {Folio}: {Comentario}", con el enlace a la app. Cuando el reportante reenvía, la app pone `Estado = Enviado` y AV-01 corre de nuevo; el folio y la `FechaEnvio` se conservan por los pasos 3 y 4.

---

## AV-02 — Valorización, tramo y aprobaciones N2–N4

**Disparador:** *Cuando se crea o modifica un elemento*, en `Averías`.

**Condición del disparador:**
```
@equals(triggerOutputs()?['body/Estado/Value'], 'Valorizado')
```

La app solo permite pasar a `Valorizado` cuando `CostoUnitarioLocal > 0`. La validación de la lista lo vuelve a exigir.

### Valorización y tramo

| # | Acción | Detalle |
|---|---|---|
| 1 | Obtener elemento + verificación de estado | Igual que en AV-01. |
| 2 | Parámetros | Igual que en AV-01. |
| 3 | Obtener elementos `Cfg_TipoCambio` | Filtro: `Title eq '{yyyy-MM actual}' and Moneda eq '{Moneda}' and Activo eq 1`. **Si está vacío:** prueba con el mes anterior, avisa al Admin por Teams "Falta el TC {Moneda} {mes}" y continúa. Si el mes anterior también falta, termina con aviso y el caso queda en `Valorizado`; cuando se cargue el TC, el Admin reprocesa el caso cambiando el estado a otro valor y de vuelta a `Valorizado`. |
| 4 | Componer `CostoUSD` | `div(float(formatNumber(mul(float(Cantidad), float(CostoUnitarioLocal)), '0.00')), float(TC.UnidadesPorUSD))`, redondeado con `formatNumber(..., '0.00')`. |
| 5 | Obtener elementos `Averías` (otros casos de la ventana) | Filtro: `UbicacionCodigo eq '{UbicacionCodigo}' and SKU eq '{SKU}' and FechaEnvio ge '{addDays(utcNow(), -VentanaFraccionamientoDias)}' and ID ne {ID}`. Todas son columnas indexadas. |
| 6 | Filtrar matriz | `Estado` no en {Rechazado, Anulado, Borrador, Devuelto para corrección} y `CostoTotalUSD` no vacío. |
| 7 | Inicializar variable `varAcum` (Float) = `CostoUSD`; *Aplicar a cada uno* → Incrementar variable con `float(item()?['CostoTotalUSD'])` | Power Automate no tiene una función para sumar matrices. Son pocos ítems, así que el bucle es barato. |
| 8 | Componer `MontoTramo` | `max(CostoUSD, variables('varAcum'))` |
| 9 | Obtener elementos `Cfg_Umbrales` | Filtro: `Activo eq 1`. Son pocas filas, así que se traen todas. |
| 10 | Filtrar matriz `ReglasPais` | `PaisCodigo = {PaisCodigo}` y vigentes (`VigenteDesde <= FechaEnvio` y (`VigenteHasta` vacío o `>= FechaEnvio`)). Si queda vacío, el mismo filtro con `PaisCodigo = '*'`. |
| 11 | Filtrar matriz `Regla` | `MontoDesdeUSD <= MontoTramo` y `MontoHastaUSD >= MontoTramo`; toma `first()`. **Si está vacío** (hueco en la configuración): avisa al Admin y aplica la fila de tramo más alto. Ante la duda se controla de más, no de menos. |
| 12 | Componer `TramoPropio` | La misma búsqueda del paso 11 pero con `CostoUSD`. `Alerta = not(equals(TramoPropio.Nivel, Regla.Nivel))`. |
| 13 | Actualizar elemento | `TipoCambioAplicado`, `CostoTotalUSD = CostoUSD`, `AcumuladoVentanaUSD = varAcum`, `AlertaFraccionamiento = Alerta`, `Tramo = Regla.Nivel`, `NivelesRequeridos = Regla.NivelesRequeridos`, `VersionRegla = Regla.Title`, `FechaValorizacion = utcNow()`, `FechaLimiteCierre = addDays(FechaEnvio, int(Regla.SLACierreDias))`. Si `NivelesRequeridos = 1`: `Estado = Pendiente ajuste Infor` y `FechaAprobacionFinal = utcNow()`; si no: `Estado = Pendiente N2` y `NivelActual = 2`. |
| 14 | Historial | `Accion = Valorizado`, `Nivel = 0`, `Actor = ControlInventarios`, desde `FechaN1` hasta ahora. |
| 15 | Condición `NivelesRequeridos = 1` | Si se cumple, salta a "Aviso de ajuste Infor". |

### Bucle de aprobaciones N2–N4

| # | Acción | Detalle |
|---|---|---|
| 16 | Inicializar variables | `varNivel` (Integer) = 2; `varPrevios` (Array) = `[toLower(ReportanteEmail), toLower(AprobadorN1.Email)]`; `varRechazado` (Boolean) = false. |
| 17 | **Hacer hasta** `or(greater(variables('varNivel'), NivelesRequeridos), variables('varRechazado'))` | ⚠️ **Cambiar los límites del Hacer hasta:** el tiempo de espera predeterminado es `PT1H` y cortaría las aprobaciones. Hay que poner **Recuento = 10** y **Tiempo de espera = `P30D`**. |
| 17.1 | Componer `Rol` | `Regla?[concat('RolN', string(variables('varNivel')))]` |
| 17.2 | Resolver aprobador | En `Cfg_Aprobadores` con `Rol`: primero país + ubicación exacta, después país + `*`, después `*` + `*`. Si no hay ninguno: aviso al Admin y termina (falló). |
| 17.3 | Segregación | Si el aprobador está en `varPrevios`, usa el suplente. Si el suplente también está, registra en el historial "Nivel {n} omitido por segregación" y sigue con el nivel siguiente. Si el nivel omitido era el último, escala al rol `Gerente de logística regional`. |
| 17.4 | Actualizar elemento | `Estado = concat('Pendiente N', varNivel)`, `NivelActual = varNivel`. |
| 17.5 | Crear una aprobación | Respuestas personalizadas: `Aprobar` / `Rechazar`. Título: `Avería {Folio} · USD {CostoUSD} · Tramo {Tramo} · N{n}`. Los detalles agregan a lo de N1 el costo local y en USD, el TC, la disposición propuesta, el valor recuperable estimado, quién aprobó los niveles anteriores con sus comentarios y, **si `AlertaFraccionamiento = Sí`**, un encabezado en negrita: "⚠ Acumulado del SKU en la ubicación en {Ventana} días: USD {varAcum}". |
| 17.6 | Esperar, recordar y escalar | Igual que los pasos 12–14 de AV-01. |
| 17.7 | **Switch** `varNivel` (2, 3, 4) → Actualizar elemento | `AprobadorN{n} = Respondio`, `FechaN{n} = utcNow()` y `ComentarioAprobacion` anexado. El Switch existe porque *Actualizar elemento* no acepta nombres de columna dinámicos. |
| 17.8 | Historial | `Accion = Aprobado` o `Rechazado`, `Nivel = n`, con la duración. |
| 17.9 | Si `Rechazar` | Actualizar elemento: `Estado = Rechazado`, `FechaAprobacionFinal`, `MotivoRechazo`. Teams al reportante, al jefe de ubicación y a Control de Inventarios. `varRechazado = true`. El rechazo exige comentario, igual que en AV-01. |
| 17.10 | Si `Aprobar` | Agrega `Respondio` a `varPrevios`. Incrementa `varNivel`. |
| 18 | Después del bucle, si `varRechazado = false` | Actualizar elemento: `Estado = Pendiente ajuste Infor`, `FechaAprobacionFinal = utcNow()`. |

### Aviso de ajuste Infor

Va a Control de Inventarios por Teams y lleva:

- Folio, código Infor de la ubicación, SKU, cantidad y costo.
- Disposición aprobada y **motivo de ajuste Infor** sugerido según la tabla de abajo.
- SLA: `SLAAjusteInforDias` días.
- Instrucción: "Registrá el ajuste en Infor y cargá en la app el N.º de ajuste y la evidencia de la disposición".

También se avisa al reportante y al jefe de la ubicación que la avería está aprobada y que deben ejecutar la disposición: separar el producto para outlet, destruirlo con acta o prepararlo para el reclamo.

| Disposición | Motivo de ajuste Infor | Nota |
|---|---|---|
| Venta outlet / como nuevo con reempaque | COMPLETAR | Normalmente es un traslado a la ubicación o el almacén de outlet, **no una baja** |
| Reparación / reacondicionamiento | COMPLETAR | Traslado al almacén de servicio técnico |
| Reclamo a proveedor / RTV / garantía | COMPLETAR | Traslado al almacén de reclamos hasta que se resuelva |
| Reclamo a transportista o aseguradora | COMPLETAR | |
| Donación / destrucción | COMPLETAR | Baja definitiva |

> Esta tabla la tiene que completar Control de Inventarios de cada país con los códigos reales de Infor. Si no se define, cada país va a usar motivos distintos y la conciliación entre Infor y la lista de averías no va a cuadrar.

---

## AV-03 — Cierre

**Disparador:** *Cuando se crea o modifica un elemento*, en `Averías`.

**Condición del disparador:**
```
@and(
  equals(triggerOutputs()?['body/Estado/Value'], 'Pendiente ajuste Infor'),
  not(empty(triggerOutputs()?['body/NumeroAjusteInfor'])),
  not(empty(triggerOutputs()?['body/EvidenciaDisposicion']))
)
```
Se escribe en una sola línea.

| # | Acción | Detalle |
|---|---|---|
| 1 | Obtener elemento + verificación | Igual que en los otros flujos. |
| 2 | Validaciones de cierre | Si `ResponsableImputable = Proveedor` y `Proveedor` está vacío, o si `NumeroAjusteInfor` ya existe en otro caso cerrado (*Obtener elementos* con `NumeroAjusteInfor eq '{x}' and ID ne {ID}`, aunque un mismo ajuste puede cubrir varios casos; en ese caso solo se avisa, no se bloquea): Teams a Control de Inventarios con lo que falta, y termina sin cerrar. |
| 3 | Actualizar elemento | `Estado = Cerrado`, `FechaCierre = utcNow()`, `CerradoATiempo = lessOrEquals(ticks(utcNow()), ticks(FechaLimiteCierre))`. |
| 4 | Historial | `Accion = Cerrado`, `Actor = ControlInventarios`, desde `FechaAprobacionFinal` hasta ahora (es la duración del ajuste en Infor). |
| 5 | Teams al reportante | "La avería {Folio} quedó cerrada (ajuste Infor {N.º})". |

---

## AV-04 — Seguimiento diario

**Disparador:** Periodicidad diaria a las 07:00, zona `(UTC-06:00) Central America`, de lunes a sábado.

| # | Acción | Detalle |
|---|---|---|
| 1 | Parámetros | |
| 2 | Obtener elementos `Averías` con `Estado eq 'Pendiente valorización'` | **Activar paginación** (Configuración → Paginación, umbral 5000). Filtrar matriz: `FechaN1 < addHours(utcNow(), -SLAValorizacionHoras)`. |
| 3 | Obtener elementos con `Estado eq 'Pendiente ajuste Infor'` | Filtrar matriz: `FechaAprobacionFinal < addDays(utcNow(), -SLAAjusteInforDias)`. |
| 4 | Obtener elementos con `Estado eq 'Pendiente N1'`, `'Pendiente N2'`, `'Pendiente N3'` o `'Pendiente N4'` | Una sola consulta con `or`. Sirve para el resumen de aprobaciones en curso a más de 48 h, solo como información, porque las escalan los propios flujos. |
| 5 | *Aplicar a cada uno* sobre `['SV','GT','HN','NI','CR','P6']` | Por país: Filtrar matriz de los pasos 2–4 → *Crear tabla HTML* (Folio, ubicación, SKU, USD y horas de atraso) → Teams a Control de Inventarios del país (pasos 2 y 3) y al Gerente de logística país (resumen con los conteos). **Si el país no tiene nada vencido, no se envía mensaje**, para que la notificación no se vuelva ruido. |

**Qué queda fuera de AV-04 a propósito:** el umbral acumulado mensual por ubicación (`UmbralAcumuladoTiendaMesUSD`) y las alertas de concentración se resuelven con **alertas de datos de Power BI**. Se crea un mosaico de tarjeta en un panel y se configura una alerta, lo que solo requiere Pro. Agrupar y sumar en Power Automate gasta muchas acciones y es difícil de mantener.

---

## Pruebas antes de salir a producción

Se prueban en un sitio o lista de prueba con los mismos nombres internos.

| Caso | Esperado |
|---|---|
| Avería de USD 40 en una tienda | N1 → valorización → `Pendiente ajuste Infor` sin N2 |
| Avería de USD 300 | N1 → valorización → N2 → `Pendiente ajuste Infor` |
| Avería de USD 6 000 en GTQ | Conversión con el TC del mes; N1–N4; `FechaLimiteCierre` = envío + 20 días |
| Tres averías de USD 120 del mismo SKU y tienda en 5 días | La tercera entra en T2 con `AlertaFraccionamiento = Sí` |
| El reportante es el jefe de tienda | N1 va al suplente |
| N1 no responde en 48 h | Recordatorio a las 24 h y escalamiento al suplente a las 48 h; ambos quedan en el historial |
| N1 devuelve y el reportante corrige | El mismo folio y la misma `FechaEnvio`; vuelve a N1 |
| Rechazo sin comentario | No se rechaza; se pide de nuevo con el comentario |
| Falta el TC del mes | Usa el mes anterior y avisa al Admin |
| Se carga el N.º de ajuste sin evidencia | No cierra |
| Cierre después de `FechaLimiteCierre` | `CerradoATiempo = No` |
| Dos ediciones seguidas en `Enviado` | Una sola aprobación N1 (verificación del paso 1) |
