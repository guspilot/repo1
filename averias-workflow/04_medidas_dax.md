# 04 — Modelo Power BI y medidas DAX

Alineado con **POL-CO-0031 v2.0**, sección 9. La política exige que todos los KPIs estén en un **tablero corporativo** que se revisa mensualmente (9.3). Las medidas que corresponden a un KPI de la política llevan la marca ★ y la sección de origen.

## Conexión (sin gateway ni TI)

- Se usa el conector **SharePoint Online List**, implementación 1.0 (`ApiVersion = 15`), porque devuelve los **nombres internos** de las columnas. Con orígenes en SharePoint Online, la actualización programada no necesita gateway.
- Para compartir el tablero, quien lo publica y quien lo consume necesitan **Power BI Pro**.
- **Datos que no están en el workflow.** Tres KPIs de la política necesitan datos de Infor o de Ventas. Sin integración, se cargan como Excel **mensuales** en una biblioteca del mismo sitio, `BI_Externos`, exportados de los reportes existentes:

| Archivo (tabla de Excel) | Columnas | Fuente | KPI que habilita |
|---|---|---|---|
| `Ext_VentasNetas.xlsx` (tabla `VentasNetas`) | Periodo (fecha, día 1 del mes), PaisCodigo, VentasNetasUSD | BI de ventas | Costo de averías vs. ventas netas [9.1] |
| `Ext_Inventario.xlsx` (tabla `Inventario`) | Periodo, PaisCodigo, InvPromCostoUSD, InvPromRetailUSD | Infor | Índice general de averías [9.1] |
| `Ext_Recepciones.xlsx` (tabla `Recepciones`) | Periodo, PaisCodigo, Proveedor, UnidadesRecibidas | Infor (recepciones) | Tasa de averías por proveedor [9.2] |
| `Ext_VentasOutlet.xlsx` (tabla `VentasOutlet`) — opcional | Periodo, PaisCodigo, CostoVendidoAveriadoUSD | BI de ventas (outlet o remate) | Rotación de inventario averiado [9.2], versión exacta |
| `Ext_Auditorias.xlsx` (tabla `Auditorias`) | Fecha, PaisCodigo, UbicacionCodigo, TipoHallazgo (Proceso / Inventario no declarado), Hallazgos | CI | Tasa de cumplimiento de la política [9.2] |

El nombre de `Proveedor` en `Ext_Recepciones` tiene que ser **el mismo texto de Infor** que CI carga en las líneas.

## Power Query

### `Averias`

```m
let
    Sitio    = "https://<tenant>.sharepoint.com/sites/<sitio-averias>",
    Lista    = SharePoint.Tables(Sitio, [ApiVersion = 15]){[Title = "Averías"]}[Items],
    Cols     = Table.SelectColumns(Lista, {
        "Id","Title","PaisCodigo","UbicacionCodigo","TipoUbicacion","MatrizAplicable","TiendaVendedoraCodigo",
        "EtapaDeteccion","TipoAveriaCodigo","Origen","CausaCodigo","Consolidado","Estado","NivelAprobacion",
        "MotivoNivel","RecurrenciaObservada","RolAprobador","VersionMatriz","DisposicionPropuesta","Recuperacion",
        "DiagnosticoST","DescuentoAutorizadoPct","CostoTotalUSD","CostoUnitarioMaxUSD","RetailTotalUSD",
        "MontoFacturableUSD","MontoRecuperadoUSD","HorasDeteccionAReporte","ReporteTardio","DiasResolucionE2E",
        "CerradoATiempo","ReportanteEmail","FechaHoraDeteccion","FechaEnvio","FechaValorizacion","FechaAprobacion",
        "FechaConsolidacion","FechaAutorizacionDisposicion","FechaLimiteCierre","FechaCierre","NumeroAjusteInfor"
    }, MissingField.UseNull),
    Tipos    = Table.TransformColumnTypes(Cols, {
        {"Id", Int64.Type}, {"CostoTotalUSD", Currency.Type}, {"CostoUnitarioMaxUSD", Currency.Type},
        {"RetailTotalUSD", Currency.Type}, {"MontoFacturableUSD", Currency.Type}, {"MontoRecuperadoUSD", Currency.Type},
        {"HorasDeteccionAReporte", type number}, {"DiasResolucionE2E", type number}, {"DescuentoAutorizadoPct", type number},
        {"Consolidado", type logical}, {"ReporteTardio", type logical}, {"CerradoATiempo", type logical},
        {"RecurrenciaObservada", type logical},
        {"FechaHoraDeteccion", type datetime}, {"FechaEnvio", type datetime}, {"FechaValorizacion", type datetime},
        {"FechaAprobacion", type datetime}, {"FechaConsolidacion", type datetime},
        {"FechaAutorizacionDisposicion", type datetime}, {"FechaLimiteCierre", type datetime}, {"FechaCierre", type datetime}
    }),
    // SharePoint guarda en UTC. Los 5 países de Centroamérica están en UTC-6, sin horario de verano.
    // Si el país 6 tiene otro huso, reemplazar el -6 por una tabla de husos por PaisCodigo.
    ALocal   = (d) => if d = null then null else DateTimeZone.RemoveZone(DateTimeZone.SwitchZone(DateTime.AddZone(d, 0), -6)),
    Fechas   = {"FechaHoraDeteccion","FechaEnvio","FechaValorizacion","FechaAprobacion","FechaConsolidacion",
                "FechaAutorizacionDisposicion","FechaLimiteCierre","FechaCierre"},
    Locales0 = List.Accumulate(Fechas, Tipos, (t, c) => Table.TransformColumns(t, {{c, ALocal, type datetime}})),
    // Las columnas de elección múltiple pueden llegar como lista: se pasan a texto separado por "; "
    Locales  = Table.TransformColumns(Locales0, {
                 {"MotivoNivel", each if _ is list then Text.Combine(List.Transform(_, Text.From), "; ") else _, type text},
                 {"Recuperacion", each if _ is list then Text.Combine(List.Transform(_, Text.From), "; ") else _, type text}}),
    Dia      = (t, src, dst) => Table.AddColumn(t, dst, each if Record.Field(_, src) = null then null else Date.From(Record.Field(_, src)), type date),
    ConDias  = Dia(Dia(Dia(Dia(Dia(Locales,
                 "FechaEnvio", "FechaEnvioDia"),
                 "FechaAprobacion", "FechaAprobacionDia"),
                 "FechaLimiteCierre", "FechaLimiteDia"),
                 "FechaCierre", "FechaCierreDia"),
                 "FechaHoraDeteccion", "FechaDeteccionDia")
in
    ConDias
```

Antes de producción hay que verificar en el tenant que las fechas del conector 1.0 llegan como `datetime` UTC. Si llegan como `datetimezone`, se quita `DateTime.AddZone`.

### `Averias_Lineas`

Se carga con el mismo patrón y las columnas `Id`, `AveriaID`, `PaisCodigo`, `UbicacionCodigo`, `SKU`, `Proveedor`, `Cantidad`, `SinSerie`, `SubtipoCodigo`, `CostoUnitarioUSD`, `CostoLineaUSD`, `RetailLineaUSD`, `OrigenImputable`, `EstadoCaso` y `FechaEnvio` (más `FechaEnvioDia`).

### Excel externos

```m
let
    Archivos = SharePoint.Files("https://<tenant>.sharepoint.com/sites/<sitio-averias>", [ApiVersion = 15]),
    Archivo  = Archivos{[Name = "Ext_VentasNetas.xlsx", #"Folder Path" = "https://<tenant>.sharepoint.com/sites/<sitio-averias>/BI_Externos/"]}[Content],
    Tabla    = Excel.Workbook(Archivo, true){[Item = "VentasNetas", Kind = "Table"]}[Data],
    Tipos    = Table.TransformColumnTypes(Tabla, {{"Periodo", type date}, {"PaisCodigo", type text}, {"VentasNetasUSD", Currency.Type}})
in
    Tipos
```

Las demás tablas externas se cargan igual. También se cargan `Cat_Ubicacion`, `Cat_TipoAveria`, `Cat_Subtipo`, `Cat_Causa`, `Averias_Historial` y `Cfg_AccesoBI`.

## Dimensiones

`Dim_Pais` y `Dim_Proveedor` se arman en **Power Query**, no en DAX. Una tabla calculada que lee de las mismas tablas con las que después se relaciona puede dar error de dependencia circular.

- **`Dim_Pais`:** referencia a `Cat_Ubicacion`, quedarse solo con `PaisCodigo` y quitar duplicados.
- **`Dim_Proveedor`:** anexar la columna `Proveedor` de `Averias_Lineas` y de `Ext_Recepciones`, quitar nulos y quitar duplicados.

```dax
Calendario =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2026, 1, 1 ), DATE ( YEAR ( TODAY () ) + 1, 12, 31 ) ),
    "Año", YEAR ( [Date] ),
    "Mes", FORMAT ( [Date], "YYYY-MM" ),
    "InicioMes", DATE ( YEAR ( [Date] ), MONTH ( [Date] ), 1 ),
    "DiaHabil", WEEKDAY ( [Date], 2 ) <= 5
)
```

En `Calendario`, renombrá `[Date]` a `Fecha` y marcala como tabla de fechas.

## Relaciones

| Desde (muchos) | Hacia (uno) | Activa |
|---|---|---|
| `Cat_Ubicacion[PaisCodigo]` | `Dim_Pais[PaisCodigo]` | Sí |
| `Averias[UbicacionCodigo]` | `Cat_Ubicacion[Title]` | Sí |
| `Averias[TipoAveriaCodigo]` | `Cat_TipoAveria[Title]` | Sí |
| `Averias[CausaCodigo]` | `Cat_Causa[Title]` | Sí |
| `Averias[FechaEnvioDia]` | `Calendario[Fecha]` | **Sí** |
| `Averias[FechaAprobacionDia]`, `[FechaLimiteDia]`, `[FechaCierreDia]`, `[FechaDeteccionDia]` | `Calendario[Fecha]` | No (se usan con `USERELATIONSHIP`) |
| `Averias_Lineas[AveriaID]` | `Averias[Id]` | Sí |
| `Averias_Lineas[Proveedor]` | `Dim_Proveedor[Proveedor]` | Sí |
| `Averias_Lineas[SubtipoCodigo]` | `Cat_Subtipo[Title]` | Sí |
| `Averias_Historial[AveriaID]` | `Averias[Id]` | Sí |
| `Ext_*[PaisCodigo]` | `Dim_Pais[PaisCodigo]` | Sí |
| `Ext_*[Periodo]` | `Calendario[Fecha]` | Sí |
| `Ext_Recepciones[Proveedor]` | `Dim_Proveedor[Proveedor]` | Sí |

El país **siempre** se filtra desde `Dim_Pais`, así el filtro y el RLS llegan tanto a las averías como a los Excel externos.

## Medidas

### Base

```dax
Averias validas =
CALCULATE ( COUNTROWS ( Averias ), NOT Averias[Estado] IN { "Borrador", "Anulado", "Rechazado" } )

Costo averias USD =
CALCULATE ( SUM ( Averias[CostoTotalUSD] ), NOT Averias[Estado] IN { "Borrador", "Anulado", "Rechazado" } )

Retail averias USD =
CALCULATE ( SUM ( Averias[RetailTotalUSD] ), NOT Averias[Estado] IN { "Borrador", "Anulado", "Rechazado" } )

Costo aprobado USD =
CALCULATE (
    SUM ( Averias[CostoTotalUSD] ),
    NOT Averias[Estado] IN { "Borrador", "Anulado", "Rechazado", "Enviado", "Pendiente valorización", "Valorizado", "Pendiente aprobación", "Devuelto para corrección" },
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

Costo acumulado YTD =
TOTALYTD ( [Costo aprobado USD], Calendario[Fecha] )

Unidades averiadas =
CALCULATE (
    SUM ( Averias_Lineas[Cantidad] ),
    NOT Averias_Lineas[EstadoCaso] IN { "Borrador", "Anulado", "Rechazado" }
)
```

### KPIs a nivel compañía [9.1]

```dax
-- ★ 9.1 Costo de averías vs. ventas netas
% Costo averias vs ventas netas =
DIVIDE ( [Costo averias USD], SUM ( Ext_VentasNetas[VentasNetasUSD] ) )

-- ★ 9.1 Índice general de averías, a costo y a retail, sobre el inventario promedio mensual
-- Con varios meses seleccionados, el denominador es el promedio de los inventarios mensuales.
Indice general averias (costo) =
DIVIDE ( [Costo averias USD], AVERAGEX ( VALUES ( Calendario[InicioMes] ), CALCULATE ( SUM ( Ext_Inventario[InvPromCostoUSD] ) ) ) )

Indice general averias (retail) =
DIVIDE ( [Retail averias USD], AVERAGEX ( VALUES ( Calendario[InicioMes] ), CALCULATE ( SUM ( Ext_Inventario[InvPromRetailUSD] ) ) ) )

-- ★ 9.1 Tiempo de resolución promedio E2E (días desde la detección hasta la disposición final), según la fecha de cierre
Dias resolucion E2E (promedio) =
CALCULATE (
    AVERAGE ( Averias[DiasResolucionE2E] ),
    Averias[Estado] = "Cerrado",
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaCierreDia] )
)

Dias resolucion E2E (mediana) =
CALCULATE (
    MEDIAN ( Averias[DiasResolucionE2E] ),
    Averias[Estado] = "Cerrado",
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaCierreDia] )
)
```

### KPIs por área [9.2]

```dax
-- ★ 9.2 Índice de averías por tipo y origen, a costo y a retail. En una matriz: tipo en filas, origen en columnas.
Indice tipo-origen (costo) =
DIVIDE (
    [Costo averias USD],
    CALCULATE ( [Costo averias USD], ALLSELECTED ( Cat_TipoAveria ), ALLSELECTED ( Averias[Origen] ) )
)

Indice tipo-origen (retail) =
DIVIDE (
    [Retail averias USD],
    CALCULATE ( [Retail averias USD], ALLSELECTED ( Cat_TipoAveria ), ALLSELECTED ( Averias[Origen] ) )
)

-- ★ 9.2 Porcentaje de inventario averiado consolidado
% consolidado (costo) =
DIVIDE ( CALCULATE ( [Costo averias USD], Averias[Consolidado] = TRUE () ), [Costo averias USD] )

% consolidado (retail) =
DIVIDE ( CALCULATE ( [Retail averias USD], Averias[Consolidado] = TRUE () ), [Retail averias USD] )

-- ★ 9.2 Tiempo de reporte promedio (horas desde la detección hasta el reporte)
Horas reporte (promedio) =
CALCULATE ( AVERAGE ( Averias[HorasDeteccionAReporte] ), NOT Averias[Estado] IN { "Borrador", "Anulado" } )

% reportes fuera de 24 h =
DIVIDE ( CALCULATE ( [Averias validas], Averias[ReporteTardio] = TRUE () ), [Averias validas] )

-- ★ 9.2 Tiempo de aprobación promedio: horas de la gerencia, desde que el caso le llega (valorizado) hasta su decisión.
-- Es lo que mide el SLA de 48 h. Se fecha por la decisión.
Horas aprobacion (promedio) =
CALCULATE (
    AVERAGEX (
        FILTER ( Averias, NOT ISBLANK ( Averias[FechaValorizacion] ) && NOT ISBLANK ( Averias[FechaAprobacion] ) ),
        DATEDIFF ( Averias[FechaValorizacion], Averias[FechaAprobacion], MINUTE ) / 60
    ),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

% aprobaciones dentro de 48 h =
CALCULATE (
    DIVIDE (
        COUNTROWS ( FILTER ( Averias, NOT ISBLANK ( Averias[FechaAprobacion] ) && DATEDIFF ( Averias[FechaValorizacion], Averias[FechaAprobacion], MINUTE ) <= 48 * 60 ) ),
        COUNTROWS ( FILTER ( Averias, NOT ISBLANK ( Averias[FechaAprobacion] ) ) )
    ),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

-- Complementaria: desde el reporte hasta la decisión, incluida la valorización
Horas reporte a decision (mediana) =
CALCULATE (
    MEDIANX (
        FILTER ( Averias, NOT ISBLANK ( Averias[FechaEnvio] ) && NOT ISBLANK ( Averias[FechaAprobacion] ) ),
        DATEDIFF ( Averias[FechaEnvio], Averias[FechaAprobacion], MINUTE ) / 60
    ),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

-- ★ 9.2 Rotación de inventario averiado
-- Inventario averiado de un día = casos aprobados todavía no cerrados en esa fecha, a costo.
Inventario averiado al dia =
VAR d = MAX ( Calendario[Fecha] )
RETURN
    CALCULATE (
        SUM ( Averias[CostoTotalUSD] ),
        REMOVEFILTERS ( Calendario ),
        NOT ISBLANK ( Averias[FechaAprobacion] ),
        Averias[FechaAprobacionDia] <= d,
        OR ( ISBLANK ( Averias[FechaCierre] ), Averias[FechaCierreDia] > d ),
        NOT Averias[Estado] IN { "Rechazado", "Anulado" }
    )

Inventario averiado promedio =
AVERAGEX ( VALUES ( Calendario[Fecha] ), [Inventario averiado al dia] )

-- Numerador exacto con el Excel de ventas outlet. Sin ese archivo se usa, como aproximación, el costo de
-- los casos cerrados con venta con descuento (lo trasladado a outlet, no necesariamente vendido).
Costo vendido con averia =
VAR Exacto = SUM ( Ext_VentasOutlet[CostoVendidoAveriadoUSD] )
VAR Aprox =
    CALCULATE (
        SUM ( Averias[CostoTotalUSD] ),
        Averias[Estado] = "Cerrado",
        Averias[DisposicionPropuesta] = "Venta con descuento (outlet / remate)",
        USERELATIONSHIP ( Calendario[Fecha], Averias[FechaCierreDia] )
    )
RETURN
    IF ( NOT ISBLANK ( Exacto ), Exacto, Aprox )

Rotacion inventario averiado =
DIVIDE ( [Costo vendido con averia], [Inventario averiado promedio] )

-- ★ 9.2 Porcentaje de recuperación de costos
% recuperacion de costos =
DIVIDE ( SUM ( Averias[MontoRecuperadoUSD] ), SUM ( Averias[MontoFacturableUSD] ) )

Pendiente de recuperar USD =
SUM ( Averias[MontoFacturableUSD] ) - SUM ( Averias[MontoRecuperadoUSD] )

-- ★ 9.2 Tasa de averías por proveedor: unidades averiadas imputables al proveedor ÷ unidades recibidas
Unidades averiadas imputables a proveedor =
CALCULATE ( [Unidades averiadas], Averias_Lineas[OrigenImputable] IN { "Proveedor local", "Proveedor importado" } )

% Tasa averias por proveedor =
DIVIDE ( [Unidades averiadas imputables a proveedor], SUM ( Ext_Recepciones[UnidadesRecibidas] ) )

-- ★ 9.2 Recurrencia de averías por SKU: combinaciones SKU-proveedor con ≥ 3 casos en los últimos 60 días
-- respecto de la fecha final del filtro. Es el mismo criterio que el piso de R1.
SKU recurrentes (60 dias) =
VAR Fin = MAX ( Calendario[Fecha] )
VAR Piso = 3
VAR Base =
    CALCULATETABLE (
        SUMMARIZE ( Averias_Lineas, Averias_Lineas[SKU], Averias_Lineas[Proveedor], "@casos", DISTINCTCOUNT ( Averias_Lineas[AveriaID] ) ),
        REMOVEFILTERS ( Calendario ),
        Averias_Lineas[FechaEnvioDia] > Fin - 60,
        Averias_Lineas[FechaEnvioDia] <= Fin,
        NOT Averias_Lineas[EstadoCaso] IN { "Borrador", "Anulado", "Rechazado" }
    )
RETURN
    COUNTROWS ( FILTER ( Base, [@casos] >= Piso ) )

-- ★ 9.2 Tasa de cumplimiento de la política, reportada por tipo de hallazgo (TipoHallazgo en filas)
Hallazgos por auditoria =
DIVIDE ( SUM ( Ext_Auditorias[Hallazgos] ), COUNTROWS ( Ext_Auditorias ) )
```

### SLA de cierre y control del procedimiento

```dax
-- Cumplimiento del SLA E2E por cohorte de vencimiento: los abiertos vencidos cuentan como incumplimiento
Vencen en periodo =
CALCULATE (
    COUNTROWS ( Averias ),
    NOT ISBLANK ( Averias[FechaLimiteCierre] ),
    Averias[FechaLimiteCierre] <= NOW (),
    NOT Averias[Estado] IN { "Rechazado", "Anulado" },
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaLimiteDia] )
)

Cumplen SLA cierre =
CALCULATE (
    COUNTROWS ( Averias ),
    Averias[FechaLimiteCierre] <= NOW (),
    Averias[Estado] = "Cerrado",
    Averias[CerradoATiempo] = TRUE (),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaLimiteDia] )
)

% cumplimiento SLA cierre =
DIVIDE ( [Cumplen SLA cierre], [Vencen en periodo] )

Abiertas vencidas =
CALCULATE (
    COUNTROWS ( Averias ),
    NOT Averias[Estado] IN { "Cerrado", "Rechazado", "Anulado", "Borrador" },
    Averias[FechaLimiteCierre] < NOW (),
    REMOVEFILTERS ( Calendario )
)

-- Carga por rol aprobador (RolAprobador en filas): para vigilar las señales del documento 03
Casos por dia habil =
DIVIDE ( [Averias validas], CALCULATE ( COUNTROWS ( Calendario ), Calendario[DiaHabil] = TRUE () ) )

% casos N3 por recurrencia =
DIVIDE (
    CALCULATE ( [Averias validas], Averias[NivelAprobacion] = "N3", CONTAINSSTRING ( Averias[MotivoNivel], "Recurrencia" ) ),
    CALCULATE ( [Averias validas], Averias[NivelAprobacion] = "N3" )
)

-- Durante el piloto en modo Observar: cuántos casos habrían ido a CI por recurrencia
Casos con recurrencia observada =
CALCULATE ( [Averias validas], Averias[RecurrenciaObservada] = TRUE () )

-- Amontonamiento justo debajo del umbral N1 (costo unitario de USD 90–100 contra USD 100–110). Más de 1.5 es sospechoso.
Ratio bajo umbral N1 =
DIVIDE (
    CALCULATE ( [Averias validas], Averias[CostoUnitarioMaxUSD] > 90, Averias[CostoUnitarioMaxUSD] <= 100 ),
    CALCULATE ( [Averias validas], Averias[CostoUnitarioMaxUSD] > 100, Averias[CostoUnitarioMaxUSD] <= 110 )
)

-- Concentración: participación del reportante principal en la ubicación filtrada
% concentracion top reportante =
VAR T = ADDCOLUMNS ( VALUES ( Averias[ReportanteEmail] ), "@c", [Costo averias USD] )
RETURN DIVIDE ( MAXX ( T, [@c] ), [Costo averias USD] )

-- λ del país para R3a (D2): casos por tienda en 30 días. Usar con un país filtrado y los últimos 90 días;
-- se copia cada trimestre a LambdaPaisTienda30d.
Lambda pais tienda 30d =
VAR Tiendas = CALCULATE ( DISTINCTCOUNT ( Cat_Ubicacion[Title] ), Cat_Ubicacion[Tipo] = "Tienda", Cat_Ubicacion[Activo] = TRUE () )
VAR Dias = DATEDIFF ( MIN ( Calendario[Fecha] ), MAX ( Calendario[Fecha] ), DAY ) + 1
VAR Casos = CALCULATE ( [Averias validas], Averias[MatrizAplicable] = "Tienda" )
RETURN DIVIDE ( Casos, Tiendas ) * 30 / Dias

-- Tiempo por paso, desde el historial (Averias_Historial[Accion] en el eje): muestra dónde se atasca el proceso
Horas por paso (mediana) =
MEDIAN ( Averias_Historial[DuracionHoras] )

% pasos fuera de SLA =
DIVIDE (
    COUNTROWS ( FILTER ( Averias_Historial, NOT ISBLANK ( Averias_Historial[SLAHoras] ) && Averias_Historial[DuracionHoras] > Averias_Historial[SLAHoras] ) ),
    COUNTROWS ( FILTER ( Averias_Historial, NOT ISBLANK ( Averias_Historial[SLAHoras] ) ) )
)
```

## Seguridad por país (RLS)

En el rol `PorPais`, sobre la tabla **`Dim_Pais`**:

```dax
VAR Paises =
    CALCULATETABLE ( VALUES ( Cfg_AccesoBI[PaisCodigo] ), Cfg_AccesoBI[Email] = USERPRINCIPALNAME () )
RETURN
    "*" IN Paises || Dim_Pais[PaisCodigo] IN Paises
```

`Cfg_AccesoBI` no se relaciona con nada. Los miembros del rol los asigna el dueño del modelo en el servicio de Power BI, sin TI.

## Alertas (sin flujo)

Las **alertas de datos** de Power BI (Pro) se configuran sobre mosaicos de tarjeta en un panel:

- `% reportes fuera de 24 h` > 10 %.
- `% aprobaciones dentro de 48 h` < 90 %.
- `Abiertas vencidas` > 0 por país.
- `Casos por dia habil` de CI > 6.
- `Ratio bajo umbral N1` > 1.5.
