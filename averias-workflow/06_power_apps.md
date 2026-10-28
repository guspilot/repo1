# 06 — Especificación de la app (Power Apps lienzo)

Es la app móvil del workflow. **Solo usa SharePoint, conector estándar**, así que funciona con la licencia de Power Apps para M365 y no requiere TI. La app **no ajusta inventario**: solo registra, muestra y cambia estados. Las reglas (nivel, aprobador, SLA) viven en los flujos, no en la app, para que no haya dos versiones de la lógica.

## Principio de diseño: una bandeja, "Mis pendientes"

Cada vez que un caso pasa a un estado pendiente, el flujo escribe a **quién** le toca. La app no deduce roles caso por caso: cada usuario abre la app y ve lo suyo, con una sola consulta delegable.

Columnas nuevas en `Averias` (ya incluidas en [`01`](01_esquema_lista.md) y en los flujos de [`05`](05_flujo_power_automate.md)):

| Columna | Tipo | La escribe |
|---|---|---|
| `AsignadoAEmail` | Una línea de texto, **indexada** | Flujo, en cada cambio a un estado pendiente (incluido el escalamiento al suplente) |
| `AsignadoRol` | Una línea de texto | Flujo |
| `AsignadoDesde` | Fecha y hora | Flujo; con ella la app muestra la antigüedad y el semáforo de SLA |

| Estado | `AsignadoAEmail` |
|---|---|
| Pendiente valorización | CI valorizador |
| Pendiente aprobación | Aprobador del nivel (o su suplente después de escalar) |
| Devuelto para corrección | Reportante |
| Pendiente diagnóstico ST | ST |
| Pendiente disposición | Gerente de Tienda o de Logística del CD |
| Pendiente autorización disposición | Gerente de Producto, CI o Compras |
| Pendiente ejecución | CI |
| Cerrado, Rechazado, Anulado | (vacío) |

## Configuración de la app

- **Configuración → General → Límite de filas de datos: 2000.** Los catálogos entran completos en colecciones. Las listas grandes (`Averias`, `Averias_Lineas`, `Averias_Historial`) se consultan **solo** con filtros delegables.
- **Formato:** teléfono, vertical.
- **Orígenes de datos:** las 11 listas de [`01`](01_esquema_lista.md).
- **Parámetro de entrada:** `?id=<ID>` abre directo el detalle del caso. Los enlaces de Teams que mandan los flujos usan este parámetro.

### `App.Formulas` (fórmulas con nombre)

```powerfx
gEmail = Lower(User().Email);

// Roles del usuario: fila propia o de suplente
gMisRoles = Filter(colAprobadores, Lower(Aprobador.Email) = gEmail || Lower(Suplente.Email) = gEmail);
gEsCI = !IsEmpty(Filter(gMisRoles, StartsWith(Rol.Value, "Control de Inventarios")));
gEsGP = !IsEmpty(Filter(gMisRoles, Rol.Value = "Gerente de Producto"));

// Semáforo de SLA para las tarjetas de la bandeja (horas desde la asignación)
gHorasSLA = Table(
    {Estado: "Pendiente valorización", Horas: 24},
    {Estado: "Pendiente aprobación", Horas: 48},
    {Estado: "Pendiente autorización disposición", Horas: 72},
    {Estado: "Pendiente ejecución", Horas: 72},
    {Estado: "Pendiente diagnóstico ST", Horas: 120},
    {Estado: "Pendiente disposición", Horas: 48},
    {Estado: "Devuelto para corrección", Horas: 24}
);
```

### `App.OnStart`

```powerfx
Concurrent(
    ClearCollect(colUbicaciones, Filter(Cat_Ubicacion, Activo = true)),
    ClearCollect(colTipos, Filter(Cat_TipoAveria, Activo = true)),
    ClearCollect(colSubtipos, Filter(Cat_Subtipo, Activo = true)),
    ClearCollect(colCausas, Filter(Cat_Causa, Activo = true)),
    ClearCollect(colAprobadores, Filter(Cfg_Aprobadores, Activo = true))
);
// Última ubicación usada en este teléfono (solo en la app móvil; en el navegador queda vacío)
LoadData(colPrefs, "prefs", true);
Set(varUbicPref, First(colPrefs).Ubicacion);
// Borrador local de líneas, por si se cortó la señal a mitad del reporte
LoadData(colLineas, "lineasBorrador", true);
```

### `App.StartScreen`

```powerfx
If(!IsBlank(Param("id")), scrDetalle, scrInicio)
```

En `scrDetalle.OnVisible`: `If(!IsBlank(Param("id")) && IsBlank(varCaso), Set(varCaso, LookUp(Averias, ID = Value(Param("id")))))`.

## Pantallas

| # | Pantalla | Quién | Qué hace |
|---|---|---|---|
| 1 | `scrInicio` | Todos | Botón **Reportar avería**, bandeja **Mis pendientes** y **Mis reportes** |
| 2 | `scrReportar` | Personal de tienda, CD y transporte | Encabezado, líneas, evidencia y envío |
| 3 | `scrDetalle` | Todos | Ficha del caso, líneas, fotos y línea de tiempo (historial). Desde acá se pasa a la pantalla de acción que corresponda |
| 4 | `scrValorizar` | CI | Proveedor, costo y retail de Infor por línea; verificación de la serie; corrección de origen y causa |
| 5 | `scrDiagnostico` | ST o Logística | Diagnóstico y N.º de informe ST |
| 6 | `scrDisposicion` | Gerente de Tienda o de Logística del CD | Confirmar la disposición física y la vía de recuperación |
| 7 | `scrDescuento` | Gerente de Producto | Cargar el % y autorizar o rechazar la venta con descuento |
| 8 | `scrCerrar` | CI | N.º de movimiento Infor, evidencia y fotos o acta |

**Aprobar la avería y validar la disposición (CI o Compras) no tiene pantalla de decisión.** Se responde en **Aprobaciones** (Teams u Outlook), como define `05`. `scrDetalle` muestra el caso completo y un botón **Ir a Aprobaciones**. Así hay una sola vía de decisión y queda registrada en el workflow [8.2.4].

---

### 1. `scrInicio`

**Galería `galPendientes`** (delegable: texto indexado + orden por fecha):

```powerfx
Sort(
    Filter(Averias, AsignadoAEmail = gEmail),
    AsignadoDesde, SortOrder.Ascending
)
```

Cada tarjeta muestra el folio, la ubicación, el estado, USD si ya está valorizado, y la antigüedad con semáforo:

```powerfx
// lblSemaforo.Fill
With(
    {h: DateDiff(ThisItem.AsignadoDesde, Now(), TimeUnit.Hours),
     sla: LookUp(gHorasSLA, Estado = ThisItem.Estado.Value, Horas)},
    If(IsBlank(sla), Color.Gray, h > sla, Color.Red, h > sla * 0.5, Color.Orange, Color.Green)
)
```

**Galería `galMisReportes`:**

```powerfx
Sort(Filter(Averias, ReportanteEmail = gEmail && Created >= DateAdd(Today(), -90, TimeUnit.Days)), Created, SortOrder.Descending)
```

`OnSelect` de ambas galerías: `Set(varCaso, ThisItem); Navigate(scrDetalle)`.

---

### 2. `scrReportar`

Se arma con un **formulario de edición `frmAveria`** sobre `Averias` (DefaultMode = Nuevo), para tener el control de **Datos adjuntos**. En el móvil, ese control abre la cámara o la galería. Las líneas van en la colección `colLineas`.

**Encabezado (tarjetas visibles):**

| Control | Fórmula clave |
|---|---|
| `cmbUbicacion` (cuadro combinado sobre `colUbicaciones`, con búsqueda por código o nombre) | `DefaultSelectedItems: Filter(colUbicaciones, Title = varUbicPref)` |
| `txtTiendaVendedora` | `Visible: cmbUbicacion.Selected.Tipo.Value = "Última milla"` |
| `ddEtapa` | `Items:` las etapas válidas para el tipo de ubicación:<br>`Switch(cmbUbicacion.Selected.Tipo.Value, "Tienda", ["Descarga en tienda","Exhibición / bodega de tienda","Devolución de cliente"], "Última milla", ["Entrega a cliente"], ["Recepción de proveedor","Almacenamiento","Picking / despacho"])` |
| `dpDeteccion` + `ddHora` + `ddMin` | `varDeteccion = DateAdd(DateAdd(dpDeteccion.SelectedDate, Value(ddHora.Selected.Value), TimeUnit.Hours), Value(ddMin.Selected.Value), TimeUnit.Minutes)` |
| `lblPlazo` | Aviso de plazo: `With({h: DateDiff(varDeteccion, Now(), TimeUnit.Hours)}, If(h >= 24, "⚠ Pasaron " & h & " h desde la detección: la política pide reportar en 24 h. Reportá igual y explicá el motivo en el resumen.", h >= 20, "Quedan " & 24 - h & " h para el plazo de 24 h", ""))` |
| `cmbTipo` (sobre `colTipos`) | Muestra `Nombre` y, debajo, `Definicion`, para que el reportante clasifique bien. |
| `ddOrigen` | Los 9 valores de la elección `Origen`. |
| `cmbCausa` | `Items: Filter(colCausas, ddOrigen.Selected.Value in Split(Origenes, ";").Value)` |
| `txtResumen` | Varias líneas, con el contador `Len(Self.Text) & "/15"`. |
| `tglConsolidado` | Texto de ayuda: "¿Ya está en la ubicación de averías?" [5.4.5]. |
| `dcvAdjuntos` (tarjeta Attachments) | `lblFotos.Text: CountRows(dcvAdjuntos.Attachments) & " de " & LookUp(colTipos, Title = cmbTipo.Selected.Title, FotosMinimas) & " fotos mínimas"` |

**Tarjetas ocultas con `Update` fijo** (el usuario no las ve):

| Columna | `Update` |
|---|---|
| `Title` | `"PENDIENTE"` |
| `PaisCodigo` | `{Value: cmbUbicacion.Selected.PaisCodigo.Value}` |
| `UbicacionCodigo` | `cmbUbicacion.Selected.Title` |
| `TipoUbicacion` | `{Value: cmbUbicacion.Selected.Tipo.Value}` |
| `MatrizAplicable` | `{Value: If(cmbUbicacion.Selected.Tipo.Value in ["Tienda","Última milla"], "Tienda", "CD")}` |
| `Moneda` | `{Value: cmbUbicacion.Selected.Moneda}` |
| `FechaHoraDeteccion` | `varDeteccion` |
| `TipoAveriaCodigo` | `cmbTipo.Selected.Title` |
| `CausaCodigo` | `cmbCausa.Selected.Title` |
| `ReportanteEmail` | `gEmail` |
| `Estado` | `{Value: "Borrador"}` |

**Líneas (`galLineas` sobre `colLineas`) y alta de una línea:**

```powerfx
// btnAgregarLinea.OnSelect (el SKU viene del control Escáner de códigos o del teclado)
Collect(colLineas, {
    SKU: Trim(txtSKU.Text), Descripcion: txtDesc.Text, Serie: Trim(txtSerie.Text),
    SinSerie: tglSinSerie.Value, Cantidad: Value(txtCant.Text), Subtipo: cmbSubtipo.Selected.Title
});
SaveData(colLineas, "lineasBorrador");
Reset(txtSKU); Reset(txtDesc); Reset(txtSerie); Reset(tglSinSerie); Reset(txtCant)

// btnAgregarLinea.DisplayMode
If(And(Len(Trim(txtSKU.Text)) >= 4, Len(txtDesc.Text) > 0, Value(txtCant.Text) > 0,
       Or(tglSinSerie.Value, Len(Trim(txtSerie.Text)) > 0)), DisplayMode.Edit, DisplayMode.Disabled)
```

**Aviso de posible duplicado** (se muestra, pero no bloquea):

```powerfx
// lblDuplicado.Visible  (las dos columnas están indexadas)
!IsEmpty(Filter(Averias_Lineas,
    UbicacionCodigo = cmbUbicacion.Selected.Title && SKU = Trim(txtSKU.Text)
    && FechaEnvio >= DateAdd(Now(), -72, TimeUnit.Hours)))
```

**Validación del envío** (en `scrReportar`, como variable de contexto o fórmula del botón):

```powerfx
// btnEnviar.DisplayMode
If(And(
    !IsBlank(cmbUbicacion.Selected), !IsBlank(ddEtapa.Selected), !IsBlank(cmbTipo.Selected),
    !IsBlank(ddOrigen.Selected), !IsBlank(cmbCausa.Selected), Len(txtResumen.Text) >= 15,
    varDeteccion <= Now(), CountRows(colLineas) >= 1,
    CountRows(dcvAdjuntos.Attachments) >= LookUp(colTipos, Title = cmbTipo.Selected.Title, FotosMinimas),
    Or(cmbUbicacion.Selected.Tipo.Value <> "Última milla", Len(txtTiendaVendedora.Text) > 0),
    !varEnviando
), DisplayMode.Edit, DisplayMode.Disabled)
```

**Envío: primero el encabezado en Borrador, luego las líneas y recién al final `Enviado`.** Si falla una línea, el caso queda en Borrador y no dispara AV-01 con un caso incompleto.

```powerfx
// btnEnviar.OnSelect
Set(varEnviando, true);
SubmitForm(frmAveria)

// frmAveria.OnSuccess
Set(varIdAveria, frmAveria.LastSubmit.ID);
IfError(
    ForAll(colLineas As L,
        Patch(Averias_Lineas, Defaults(Averias_Lineas), {
            Title: "PENDIENTE", AveriaID: varIdAveria,
            PaisCodigo: frmAveria.LastSubmit.PaisCodigo.Value,
            UbicacionCodigo: frmAveria.LastSubmit.UbicacionCodigo,
            SKU: L.SKU, DescripcionProducto: L.Descripcion,
            NumeroSerie: If(L.SinSerie, "SIN SERIE", L.Serie), SinSerie: L.SinSerie,
            Cantidad: L.Cantidad, SubtipoCodigo: L.Subtipo, EstadoCaso: "Borrador"
        })
    );
    Patch(Averias, LookUp(Averias, ID = varIdAveria), {Estado: {Value: "Enviado"}});
    ClearCollect(colPrefs, {Ubicacion: cmbUbicacion.Selected.Title}); SaveData(colPrefs, "prefs");
    Clear(colLineas); SaveData(colLineas, "lineasBorrador");
    Notify("Avería reportada. Te avisamos por Teams cada vez que avance.", NotificationType.Success);
    ResetForm(frmAveria); Navigate(scrInicio),
    // Si algo falló
    Notify("No se guardaron todas las líneas. El reporte quedó en Borrador en 'Mis reportes': abrilo y reenviá.", NotificationType.Error)
);
Set(varEnviando, false)

// frmAveria.OnFailure
Notify("No se pudo guardar: " & frmAveria.Error, NotificationType.Error); Set(varEnviando, false)
```

> **Sin señal:** las listas de SharePoint no admiten el modo sin conexión nativo de Power Apps (ese modo es solo para Dataverse). Lo que sí funciona es que las **líneas** se guardan localmente con `SaveData` en cada alta, así que si se corta la señal no se pierden. Las fotos y el encabezado necesitan conexión para enviarse. Esto funciona solo en la app móvil; en el navegador, `SaveData` no persiste.

---

### 3. `scrDetalle`

- **Ficha:** campos de solo lectura de `varCaso` y la galería de líneas `Filter(Averias_Lineas, AveriaID = varCaso.ID)`, que es delegable.
- **Fotos:** se muestran con un formulario de visualización sobre `varCaso`, que incluye la tarjeta de datos adjuntos.
- **Línea de tiempo:** `Sort(Filter(Averias_Historial, AveriaID = varCaso.ID), FechaFin, SortOrder.Descending)`. Muestra la acción, el actor, la duración frente al SLA y el comentario.
- **Comentar** [8.2.5]: cualquiera que participe en el caso puede dejar un comentario. Así toda la comunicación queda en el ticket.

```powerfx
// btnComentar.OnSelect
Patch(Averias_Historial, Defaults(Averias_Historial), {
    Title: varCaso.Title, AveriaID: varCaso.ID, Accion: {Value: "Comentario"},
    Actor: {Claims: "i:0#.f|membership|" & gEmail, Email: gEmail, DisplayName: User().FullName,
            Department: "", JobTitle: "", Picture: ""},
    FechaInicio: Now(), FechaFin: Now(), Comentario: txtComentario.Text
});
Patch(Averias, varCaso, {Comentarios: User().FullName & ": " & txtComentario.Text});
Reset(txtComentario)
```

Para eso hay que agregar `Comentario` a la elección `Accion` de `Averias_Historial`.

**Botón de acción según el estado y quién mira** (solo se muestra si el caso está asignado a este usuario):

```powerfx
// btnAccion.Visible
Lower(varCaso.AsignadoAEmail) = gEmail

// btnAccion.Text
Switch(varCaso.Estado.Value,
    "Pendiente valorización", "Valorizar",
    "Pendiente aprobación", "Ir a Aprobaciones",
    "Pendiente diagnóstico ST", "Registrar diagnóstico",
    "Pendiente disposición", "Definir disposición",
    "Pendiente autorización disposición", If(varCaso.DisposicionPropuesta.Value = "Venta con descuento (outlet / remate)", "Autorizar descuento", "Ir a Aprobaciones"),
    "Pendiente ejecución", "Registrar ejecución",
    "Devuelto para corrección", "Corregir y reenviar",
    "")

// btnAccion.OnSelect
Switch(Self.Text,
    "Valorizar", Navigate(scrValorizar),
    "Registrar diagnóstico", Navigate(scrDiagnostico),
    "Definir disposición", Navigate(scrDisposicion),
    "Autorizar descuento", Navigate(scrDescuento),
    "Registrar ejecución", Navigate(scrCerrar),
    "Corregir y reenviar", Navigate(scrReportar),   // en modo edición sobre varCaso, con sus líneas cargadas en colLineas
    "Ir a Aprobaciones", Launch("https://teams.microsoft.com/l/app/" & varAppIdAprobaciones)
)
```

`varAppIdAprobaciones` es el ID de la app Aprobaciones de Teams en el tenant. Si nadie lo tiene, el botón puede abrir `https://make.powerautomate.com/approvals/received`, la vista web de aprobaciones recibidas.

Si el caso está en **Borrador o Devuelto** y lo abre el reportante, aparece además el botón **Anular**: `Patch(Averias, varCaso, {Estado: {Value: "Anulado"}})`, con confirmación.

---

### 4. `scrValorizar` (CI)

**Galería `galVal`** sobre `Filter(Averias_Lineas, AveriaID = varCaso.ID)`. Cada fila tiene `txtProv`, `txtCosto`, `txtRetail`, `tglSinSerieOK` (CI confirma que el SKU no se maneja con serie en Infor) y, arriba, `ddOrigenCI` y `cmbCausaCI` para corregir el encabezado.

```powerfx
// btnGuardarValorizacion.DisplayMode: todas las líneas completas
If(IsEmpty(Filter(galVal.AllItems,
        IsBlank(txtProv.Text) || Value(txtCosto.Text) <= 0 || Value(txtRetail.Text) <= 0
        || (SinSerie && !tglSinSerieOK.Value))),
   DisplayMode.Edit, DisplayMode.Disabled)

// btnGuardarValorizacion.OnSelect
IfError(
    ForAll(galVal.AllItems As G,
        Patch(Averias_Lineas, LookUp(Averias_Lineas, ID = G.ID), {
            Proveedor: Trim(G.txtProv.Text),
            CostoUnitarioLocal: Value(G.txtCosto.Text),
            PrecioRetailUnitarioLocal: Value(G.txtRetail.Text)
        })
    );
    Patch(Averias, varCaso, {
        Origen: {Value: ddOrigenCI.Selected.Value},
        CausaCodigo: cmbCausaCI.Selected.Title,
        ValorizadorEmail: gEmail,
        Estado: {Value: "Valorizado"}
    });
    Notify("Valorizado. El flujo calcula el nivel y envía la aprobación.", NotificationType.Success);
    Navigate(scrInicio),
    Notify("Error al guardar: " & FirstError.Message, NotificationType.Error)
)
```

Si una línea tiene `SinSerie = Sí` y CI **no** lo confirma, el botón queda deshabilitado. En ese caso CI devuelve el caso al reportante con un comentario, para que cargue la serie.

---

### 5. `scrDiagnostico` (ST o Logística)

```powerfx
// btnGuardarDiag.OnSelect
Patch(Averias, varCaso, {
    DiagnosticoST: {Value: ddDiag.Selected.Value},
    NumeroInformeST: txtInformeST.Text,
    FechaDiagnosticoST: Now(),
    Estado: {Value: "Pendiente disposición"}
});
Navigate(scrInicio)
```

El `DisplayMode` exige el diagnóstico y el N.º de informe.

---

### 6. `scrDisposicion` (Gerente de Tienda o de Logística del CD)

```powerfx
// ddDisposicion.Items: quita Reincorporación si ST dijo No reparable, y RTV si el origen no es un proveedor
Filter(
    Choices(Averias.DisposicionPropuesta),
    !(Value = "Reincorporación (reparación ST)" && varCaso.DiagnosticoST.Value = "No reparable"),
    !(Value = "Devolución a proveedor local" && varCaso.Origen.Value <> "Proveedor local"),
    !(Value = "Devolución a proveedor internacional" && varCaso.Origen.Value <> "Proveedor importado")
)

// ddDisposicion.Default: la sugerida por el subtipo de la primera línea, o la propuesta original
Coalesce(varCaso.DisposicionPropuesta.Value,
    LookUp(colSubtipos, Title = First(Filter(Averias_Lineas, AveriaID = varCaso.ID)).SubtipoCodigo, DisposicionSugerida))

// btnProponer.OnSelect
Patch(Averias, varCaso, {
    DisposicionPropuesta: {Value: ddDisposicion.Selected.Value},
    Recuperacion: ForAll(cmbRecuperacion.SelectedItems, {Value: ThisRecord.Value}),
    Estado: {Value: "Disposición propuesta"}
});
Navigate(scrInicio)
```

`cmbRecuperacion` (selección múltiple) se precarga con la `RecuperacionSugerida` de la causa.

---

### 7. `scrDescuento` (Gerente de Producto, SLA de 72 h [7.6])

```powerfx
// btnAutorizar.OnSelect   (sldDescuento: 5–90 %)
Patch(Averias, varCaso, {
    DescuentoAutorizadoPct: sldDescuento.Value,
    Estado: {Value: "Pendiente ejecución"}
});
Patch(Averias_Historial, Defaults(Averias_Historial), {
    Title: varCaso.Title, AveriaID: varCaso.ID, Accion: {Value: "Disposición autorizada"},
    FechaInicio: varCaso.AsignadoDesde, FechaFin: Now(),
    Comentario: "Descuento " & sldDescuento.Value & " %. " & txtNota.Text
});
Navigate(scrInicio)

// btnRechazar.OnSelect (el motivo es obligatorio)
Patch(Averias, varCaso, {Estado: {Value: "Pendiente disposición"}, Comentarios: "GP rechaza descuento: " & txtNota.Text});
Navigate(scrInicio)
```

La pantalla muestra el costo y el retail del caso, el **precio resultante** (`RetailTotalUSD × (1 − %)`) y el **margen sobre costo**, para que el Gerente de Producto decida con números. AV-03 detecta el cambio de estado y registra `AutorizadorDisposicion`.

---

### 8. `scrCerrar` (CI)

Es un formulario de edición sobre `varCaso`, con las tarjetas `NumeroAjusteInfor` y `EvidenciaDisposicion` y los **datos adjuntos** (para el acta y las fotos de la destrucción [7.8.2]).

```powerfx
// btnCerrar.DisplayMode
If(Len(dcvAjuste.Text) >= 4 && Len(dcvEvidencia.Text) > 0, DisplayMode.Edit, DisplayMode.Disabled)

// btnCerrar.OnSelect
SubmitForm(frmCerrar)

// frmCerrar.OnSuccess
Notify("Registrado. El flujo cierra el caso y calcula el E2E.", NotificationType.Success); Navigate(scrInicio)
```

Para destrucción o donación, AV-04 exige fotos **posteriores** a la autorización. La pantalla lo avisa: "Adjuntá el acta firmada y las fotos de la destrucción o entrega".

---

## Pruebas de la app (además de las 20 de los flujos)

| Caso | Esperado |
|---|---|
| Reporte sin fotos suficientes | El botón Enviar queda deshabilitado y muestra el contador de fotos |
| Línea sin serie y sin marcar "sin serie" | No se puede agregar la línea |
| Se corta la señal con 3 líneas cargadas | Al reabrir la app, las 3 líneas siguen (solo en la app móvil) |
| Falla el guardado de la segunda línea | El encabezado queda en Borrador y el mensaje lo indica; el flujo no se dispara |
| Reportante de tienda | Solo ve Reportar y Mis reportes; Mis pendientes vacío salvo los Devueltos |
| CI valoriza con un retail en 0 | El botón queda deshabilitado |
| Diagnóstico No reparable | La opción Reincorporación no aparece en la disposición |
| Escalamiento al suplente | El caso aparece en la bandeja del suplente y desaparece de la del titular |
| Abrir el enlace de Teams `?id=123` | Abre directo el detalle del caso 123 |
| Usuario de GT abre el caso de SV por enlace | Lo ve. Es la limitación aceptada en 01: no hay permisos por ítem |
