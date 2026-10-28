# 04 — Modelo Power BI y medidas DAX

## Conexión (sin gateway ni TI)

- Conector **SharePoint Online List** con la cuenta propia. Para orígenes SharePoint Online la actualización programada en el servicio **no necesita gateway**.
- Publicar en un área de trabajo propia. Para compartir hace falta **Power BI Pro** para quien publica y para quien consume (o capacidad Premium/Fabric). Si los gerentes de país no tienen Pro, ese es el único bloqueo real de licencias y hay que saberlo antes de construir.
- Uso la **implementación 1.0** del conector porque devuelve los **nombres internos** de las columnas. Por eso el esquema exige crearlas sin tildes ni espacios. Además, como la lista guarda copias en texto de los códigos (`UbicacionCodigo`, `TipoAveriaCodigo`, `CausaCodigo`, `ReportanteEmail`), no hace falta expandir columnas de búsqueda ni de persona.

## Power Query: tabla `Averias`

```m
let
    Sitio      = "https://<tenant>.sharepoint.com/sites/<sitio-averias>",
    Origen     = SharePoint.Tables(Sitio, [ApiVersion = 15]),
    Lista      = Origen{[Title = "Averías"]}[Items],
    Columnas   = Table.SelectColumns(Lista, {
        "Id", "Title", "PaisCodigo", "UbicacionCodigo", "TipoUbicacion", "EtapaDeteccion",
        "TipoAveriaCodigo", "CausaCodigo", "ResponsableImputable", "DisposicionPropuesta",
        "SKU", "Proveedor", "Cantidad", "Moneda", "CostoTotalLocal", "CostoTotalUSD",
        "ValorRecuperableEstUSD", "MontoRecuperadoUSD", "Estado", "Tramo", "NivelesRequeridos",
        "VersionRegla", "AlertaFraccionamiento", "ReporteTardio", "CerradoATiempo",
        "ReportanteEmail", "FechaDeteccion", "FechaEnvio", "FechaValorizacion",
        "FechaAprobacionFinal", "FechaLimiteCierre", "FechaCierre", "NumeroAjusteInfor"
    }, MissingField.UseNull),
    Tipos      = Table.TransformColumnTypes(Columnas, {
        {"Id", Int64.Type}, {"Cantidad", Int64.Type}, {"NivelesRequeridos", Int64.Type},
        {"CostoTotalLocal", type number}, {"CostoTotalUSD", Currency.Type},
        {"ValorRecuperableEstUSD", Currency.Type}, {"MontoRecuperadoUSD", Currency.Type},
        {"AlertaFraccionamiento", type logical}, {"ReporteTardio", type logical},
        {"CerradoATiempo", type logical}, {"FechaDeteccion", type date},
        {"FechaEnvio", type datetime}, {"FechaValorizacion", type datetime},
        {"FechaAprobacionFinal", type datetime}, {"FechaLimiteCierre", type datetime},
        {"FechaCierre", type datetime}
    }),
    // SharePoint guarda en UTC. Los 5 países de Centroamérica están en UTC-6 sin horario de verano.
    // Si el país 6 tiene otro huso, hay que reemplazar el -6 fijo por una tabla de husos por PaisCodigo.
    ALocal     = (d) => if d = null then null
                 else DateTimeZone.RemoveZone(DateTimeZone.SwitchZone(DateTime.AddZone(d, 0), -6)),
    Locales    = List.Accumulate(
                    {"FechaEnvio", "FechaValorizacion", "FechaAprobacionFinal", "FechaLimiteCierre", "FechaCierre"},
                    Tipos,
                    (t, c) => Table.TransformColumns(t, {{c, ALocal, type datetime}})),
    // Columnas de fecha (sin hora) para las relaciones con Calendario
    ConDias    = Table.AddColumn(
                 Table.AddColumn(
                 Table.AddColumn(
                 Table.AddColumn(Locales,
                    "FechaEnvioDia",       each if [FechaEnvio] = null then null else Date.From([FechaEnvio]), type date),
                    "FechaAprobacionDia",  each if [FechaAprobacionFinal] = null then null else Date.From([FechaAprobacionFinal]), type date),
                    "FechaLimiteDia",      each if [FechaLimiteCierre] = null then null else Date.From([FechaLimiteCierre]), type date),
                    "FechaCierreDia",      each if [FechaCierre] = null then null else Date.From([FechaCierre]), type date)
in
    ConDias
```

Tablas adicionales, cargadas con el mismo patrón: `Averias_Historial`, `Cat_Ubicacion`, `Cat_TipoAveria`, `Cat_Causa` y `Cfg_AccesoBI` (para RLS).

## Relaciones

| Desde (muchos) | Hacia (uno) | Activa |
|---|---|---|
| `Averias[FechaEnvioDia]` | `Calendario[Fecha]` | **Sí** |
| `Averias[FechaAprobacionDia]` | `Calendario[Fecha]` | No (se usa con `USERELATIONSHIP`) |
| `Averias[FechaLimiteDia]` | `Calendario[Fecha]` | No |
| `Averias[FechaCierreDia]` | `Calendario[Fecha]` | No |
| `Averias[UbicacionCodigo]` | `Cat_Ubicacion[Title]` | Sí |
| `Averias[TipoAveriaCodigo]` | `Cat_TipoAveria[Title]` | Sí |
| `Averias[CausaCodigo]` | `Cat_Causa[Title]` | Sí |
| `Averias_Historial[AveriaID]` | `Averias[Id]` | Sí |

El **país siempre se filtra con `Cat_Ubicacion[PaisCodigo]`** (la dimensión), no con la columna de la tabla de hechos, para que el filtro de país y el RLS actúen sobre una sola columna.

## Tabla de fechas

```dax
Calendario =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2026, 1, 1 ), DATE ( YEAR ( TODAY () ) + 1, 12, 31 ) ),
    "Año", YEAR ( [Date] ),
    "Mes", FORMAT ( [Date], "YYYY-MM" ),
    "MesNum", MONTH ( [Date] ),
    "Semana", WEEKNUM ( [Date], 2 ),
    "DiaHabil", WEEKDAY ( [Date], 2 ) <= 5
)
```

Renombrá `[Date]` a `Fecha` y marcala como tabla de fechas.

## Medidas

Las medidas están agrupadas por pregunta de negocio. Las que piden explícitamente están marcadas con ★.

### Volumen: averías por país y tipo ★

```dax
Averias =
COUNTROWS ( Averias )

Averias enviadas =
CALCULATE ( [Averias], NOT ISBLANK ( Averias[FechaEnvio] ) )

-- Excluye borradores, anulados y rechazados: es el volumen "real" de avería
Averias validas =
CALCULATE (
    [Averias],
    NOT Averias[Estado] IN { "Borrador", "Anulado", "Rechazado" }
)

-- Participación de cada tipo dentro de lo que está filtrado (p. ej. dentro del país)
% del total (tipo) =
DIVIDE (
    [Averias validas],
    CALCULATE ( [Averias validas], ALLSELECTED ( Cat_TipoAveria ) )
)

-- Normaliza por la cantidad de tiendas para comparar países de distinto tamaño
Averias por tienda por mes =
VAR Tiendas =
    CALCULATE ( DISTINCTCOUNT ( Cat_Ubicacion[Title] ), Cat_Ubicacion[Tipo] = "Tienda", Cat_Ubicacion[Activo] = TRUE () )
VAR Meses =
    DISTINCTCOUNT ( Calendario[Mes] )
RETURN
    DIVIDE ( CALCULATE ( [Averias validas], Cat_Ubicacion[Tipo] = "Tienda" ), Tiendas * Meses )
```

Para "averías por país y tipo" se usa una matriz con `Cat_Ubicacion[PaisCodigo]` en filas, `Cat_TipoAveria[Nombre]` en columnas y `[Averias validas]` y `[% del total (tipo)]` como valores.

### Costo ★

```dax
Costo USD =
CALCULATE ( SUM ( Averias[CostoTotalUSD] ), NOT Averias[Estado] IN { "Borrador", "Anulado", "Rechazado" } )

-- Costo aprobado, fechado por la fecha de aprobación final (es cuando la pérdida queda reconocida)
Costo aprobado USD =
CALCULATE (
    SUM ( Averias[CostoTotalUSD] ),
    Averias[Estado] IN { "Pendiente ajuste Infor", "Cerrado" },
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

-- ★ Costo acumulado en el año (se reinicia en enero)
Costo acumulado YTD =
TOTALYTD ( [Costo aprobado USD], Calendario[Fecha] )

-- ★ Costo acumulado continuo, desde el inicio del proyecto (para la curva de tendencia)
Costo acumulado =
VAR FechaMax = MAX ( Calendario[Fecha] )
RETURN
    CALCULATE ( [Costo aprobado USD], Calendario[Fecha] <= FechaMax, ALL ( Calendario ) )

Costo acumulado año anterior =
CALCULATE ( [Costo acumulado YTD], SAMEPERIODLASTYEAR ( Calendario[Fecha] ) )

Recuperado USD =
CALCULATE (
    SUM ( Averias[MontoRecuperadoUSD] ),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

Perdida neta USD =
[Costo aprobado USD] - [Recuperado USD]

% recuperado =
DIVIDE ( [Recuperado USD], [Costo aprobado USD] )

-- Cuánto de lo imputable a terceros se recupera de verdad
% recuperado imputable a terceros =
VAR Imputable =
    CALCULATE ( [Costo aprobado USD], Averias[ResponsableImputable] IN { "Proveedor", "Transportista", "Aseguradora" } )
VAR Recup =
    CALCULATE ( [Recuperado USD], Averias[ResponsableImputable] IN { "Proveedor", "Transportista", "Aseguradora" } )
RETURN
    DIVIDE ( Recup, Imputable )
```

### Tiempo de aprobación ★

Va de `FechaEnvio` a `FechaAprobacionFinal` (incluye N1, valorización y N2–N4) y se fecha por la aprobación final. La **mediana** es la cifra principal: la distribución tiene cola larga y el promedio la exagera.

```dax
Horas aprobacion (mediana) =
CALCULATE (
    MEDIANX (
        FILTER ( Averias, NOT ISBLANK ( Averias[FechaEnvio] ) && NOT ISBLANK ( Averias[FechaAprobacionFinal] ) ),
        DATEDIFF ( Averias[FechaEnvio], Averias[FechaAprobacionFinal], MINUTE ) / 60
    ),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

Horas aprobacion (promedio) =
CALCULATE (
    AVERAGEX (
        FILTER ( Averias, NOT ISBLANK ( Averias[FechaEnvio] ) && NOT ISBLANK ( Averias[FechaAprobacionFinal] ) ),
        DATEDIFF ( Averias[FechaEnvio], Averias[FechaAprobacionFinal], MINUTE ) / 60
    ),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

Horas aprobacion (P90) =
CALCULATE (
    PERCENTILEX.INC (
        FILTER ( Averias, NOT ISBLANK ( Averias[FechaEnvio] ) && NOT ISBLANK ( Averias[FechaAprobacionFinal] ) ),
        DATEDIFF ( Averias[FechaEnvio], Averias[FechaAprobacionFinal], MINUTE ) / 60,
        0.9
    ),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaAprobacionDia] )
)

-- Por nivel, desde el historial: dónde se atasca (poner Averias_Historial[Nivel] en el eje)
Horas por nivel (mediana) =
MEDIANX (
    FILTER (
        Averias_Historial,
        Averias_Historial[Accion] IN { "Aprobado", "Rechazado", "Devuelto", "Valorizado" }
    ),
    Averias_Historial[DuracionHoras]
)

% aprobaciones fuera de SLA por nivel =
VAR SLA = 24
RETURN
    DIVIDE (
        COUNTROWS ( FILTER ( Averias_Historial, Averias_Historial[Accion] IN { "Aprobado", "Rechazado", "Devuelto" } && Averias_Historial[DuracionHoras] > SLA ) ),
        COUNTROWS ( FILTER ( Averias_Historial, Averias_Historial[Accion] IN { "Aprobado", "Rechazado", "Devuelto" } ) )
    )

Escalamientos a suplente =
CALCULATE ( COUNTROWS ( Averias_Historial ), Averias_Historial[Accion] = "Escalado a suplente" )
```

> En `% aprobaciones fuera de SLA por nivel` el 24 está fijo. Si `SLAAprobacionHorasPorNivel` llega a variar por tramo, conviene que el flujo escriba en `Averias_Historial` una columna `SLAHoras` por fila y comparar contra ella.

### Cierre a tiempo ★

Van dos medidas, porque miden cosas distintas y conviene tener las dos a la vista:

- **`% cerrado a tiempo`**: de lo que se cerró en el período, cuánto se cerró dentro del SLA. Mide la **calidad del cierre**, pero tiene un sesgo: los casos que siguen abiertos y vencidos no cuentan, así que el indicador **mejora cuando no se cierra nada**.
- **`% cumplimiento SLA cierre`** (recomendado como KPI principal): toma la cohorte de casos cuyo plazo **vencía** en el período y cuenta cuántos se cerraron a tiempo. Los abiertos vencidos cuentan como incumplimiento.

```dax
Cerradas =
CALCULATE (
    [Averias],
    Averias[Estado] = "Cerrado",
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaCierreDia] )
)

Cerradas a tiempo =
CALCULATE (
    [Averias],
    Averias[Estado] = "Cerrado",
    Averias[CerradoATiempo] = TRUE (),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaCierreDia] )
)

-- ★ Calidad del cierre (sobre lo cerrado)
% cerrado a tiempo =
DIVIDE ( [Cerradas a tiempo], [Cerradas] )

-- Cohorte: casos cuyo plazo venció en el período (ya vencido a hoy)
Vencen en periodo =
CALCULATE (
    [Averias],
    NOT ISBLANK ( Averias[FechaLimiteCierre] ),
    Averias[FechaLimiteCierre] <= NOW (),
    NOT Averias[Estado] IN { "Rechazado", "Anulado" },
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaLimiteDia] )
)

Cumplen SLA cierre =
CALCULATE (
    [Averias],
    Averias[FechaLimiteCierre] <= NOW (),
    Averias[Estado] = "Cerrado",
    Averias[CerradoATiempo] = TRUE (),
    USERELATIONSHIP ( Calendario[Fecha], Averias[FechaLimiteDia] )
)

-- ★ KPI principal recomendado
% cumplimiento SLA cierre =
DIVIDE ( [Cumplen SLA cierre], [Vencen en periodo] )

-- Backlog vencido a hoy (independiente del filtro de fecha)
Abiertas vencidas =
CALCULATE (
    [Averias],
    NOT Averias[Estado] IN { "Cerrado", "Rechazado", "Anulado", "Borrador" },
    Averias[FechaLimiteCierre] < NOW (),
    REMOVEFILTERS ( Calendario )
)

-- Aprobadas que siguen sin ajuste en Infor más allá del SLA (3 días): es el riesgo de inventario descuadrado
Pendientes ajuste Infor vencidas =
CALCULATE (
    [Averias],
    Averias[Estado] = "Pendiente ajuste Infor",
    Averias[FechaAprobacionFinal] < NOW () - 3,
    REMOVEFILTERS ( Calendario )
)
```

### Control y antifraude

```dax
% averias con alerta de fraccionamiento =
DIVIDE ( CALCULATE ( [Averias validas], Averias[AlertaFraccionamiento] = TRUE () ), [Averias validas] )

% reportes tardios =
DIVIDE ( CALCULATE ( [Averias validas], Averias[ReporteTardio] = TRUE () ), [Averias validas] )

-- Participación del reportante principal dentro de la ubicación filtrada. Más del 60 % en una tienda es para revisar.
% concentracion top reportante =
VAR PorReportante =
    ADDCOLUMNS ( VALUES ( Averias[ReportanteEmail] ), "@c", [Costo USD] )
RETURN
    DIVIDE ( MAXX ( PorReportante, [@c] ), [Costo USD] )

-- Amontonamiento bajo el umbral N2 (B: 250). Un valor mayor que 1.5 es sospechoso.
Ratio bajo umbral N2 =
VAR U = 250
VAR Debajo = CALCULATE ( [Averias validas], Averias[CostoTotalUSD] >= U - 50, Averias[CostoTotalUSD] < U )
VAR Encima = CALCULATE ( [Averias validas], Averias[CostoTotalUSD] >= U, Averias[CostoTotalUSD] < U + 50 )
RETURN
    DIVIDE ( Debajo, Encima )

-- λ del país para R3a (ver 00_contexto_politica.md, D2): casos por tienda en 30 días.
-- Usar con un país filtrado y los últimos 90 días; se copia a LambdaPaisTienda30d cada trimestre.
-- El k de cada tienda sale de Cfg_TablaPoisson (columna K_alfa_1_0) con λ × FactorTamano.
Lambda pais tienda 30d =
VAR Tiendas =
    CALCULATE ( DISTINCTCOUNT ( Cat_Ubicacion[Title] ), Cat_Ubicacion[Tipo] = "Tienda", Cat_Ubicacion[Activo] = TRUE () )
VAR Dias =
    DATEDIFF ( MIN ( Calendario[Fecha] ), MAX ( Calendario[Fecha] ), DAY ) + 1
VAR Casos =
    CALCULATE ( [Averias validas], Cat_Ubicacion[Tipo] = "Tienda" )
RETURN
    DIVIDE ( Casos, Tiendas ) * 30 / Dias

% rechazo =
DIVIDE ( CALCULATE ( [Averias], Averias[Estado] = "Rechazado" ), [Averias enviadas] )
```

### Simulación de umbrales (para recalibrar los escenarios)

Se crea un parámetro "qué pasaría si" con *Modelado → Nuevo parámetro → Rango numérico*: nombre `Umbral N2`, de 50 a 2 000, con incremento de 50. Power BI genera la tabla y la medida `[Valor de Umbral N2]`.

```dax
Simulacion casos N2 =
CALCULATE ( [Averias validas], Averias[CostoTotalUSD] >= [Valor de Umbral N2] )

Simulacion % costo cubierto N2 =
DIVIDE (
    CALCULATE ( [Costo USD], Averias[CostoTotalUSD] >= [Valor de Umbral N2] ),
    [Costo USD]
)

Simulacion casos N2 por dia habil =
DIVIDE ( [Simulacion casos N2], CALCULATE ( COUNTROWS ( Calendario ), Calendario[DiaHabil] = TRUE () ) )
```

Lo mismo sirve para N3 y N4 con sus propios parámetros.

## Seguridad por país (RLS)

`Cfg_AccesoBI` es una lista con columnas `Email` y `PaisCodigo`; `*` da acceso a todos los países (plantilla en `config/acceso_bi_plantilla.csv`). En el rol `PorPais`, sobre la tabla `Cat_Ubicacion`:

```dax
VAR Paises =
    CALCULATETABLE ( VALUES ( Cfg_AccesoBI[PaisCodigo] ), Cfg_AccesoBI[Email] = USERPRINCIPALNAME () )
RETURN
    "*" IN Paises || Cat_Ubicacion[PaisCodigo] IN Paises
```

`Cfg_AccesoBI` no se relaciona con nada; si se relacionara, el filtro del rol se propagaría al revés. Los miembros del rol se asignan en el servicio de Power BI, en la configuración de seguridad del modelo semántico, y eso lo hace el dueño del modelo sin TI.
