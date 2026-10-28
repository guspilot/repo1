# 01 — Esquema SharePoint: lista "Averías" y listas de soporte

## Regla de oro antes de crear columnas

El **nombre interno** de una columna se fija cuando la creás y no cambia nunca. Power Automate, Power Apps y Power BI usan ese nombre interno. Por eso:

1. Creá cada columna con el **nombre interno de la tabla** (sin tildes, sin espacios, sin ñ).
2. Después renombrala con el **nombre visible**.

Si se crea "Fecha de aprobación" directo, el nombre interno queda `Fecha_x0020_de_x0020_aprobaci_x00f3_n` y rompe fórmulas en los tres productos.

## Sitio y permisos (sin TI)

- Un solo sitio de equipo o de comunicación del que el equipo de Logística Regional sea **propietario**. Si ya existe uno, usalo; crear listas, columnas, índices, validaciones y vistas lo hace un propietario del sitio sin TI.
- Una sola lista regional (no una por país): el modelo de Power BI, los flujos y la app son únicos y se parametrizan por `PaisCodigo`.
- Grupos del sitio: `Averías - Reportantes` (Colaborar), `Averías - Aprobadores` (Colaborar), `Averías - Admin` (Control total: Logística regional). Los catálogos y la configuración se editan solo con `Averías - Admin` y Control de Inventarios. Para eso se rompe la herencia de permisos **de la lista**, no de cada ítem, y eso lo hace un propietario del sitio.
- **Limitación aceptada:** sin romper permisos por ítem, un usuario de GT que entre directo a la lista en SharePoint puede ver ítems de SV. La app filtra por país y Power BI aplica RLS. Para averías el riesgo es bajo; no vale la pena el costo operativo de los permisos por ítem (además degradan la lista pasados unos miles de ítems).

## Lista principal: `Averias` (nombre visible: Averías)

Tipos: nombres de la interfaz de SharePoint en español. "Lo llena" indica quién escribe el campo: **App** (Power Apps), **Flujo** (Power Automate) o **Sistema** (SharePoint).

### A. Identificación y ubicación

| Nombre interno | Nombre visible | Tipo | Obligatorio | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `Title` | Folio | Una línea de texto | Sí | App (temporal) → Flujo | La app escribe `PENDIENTE`; el flujo AV-01 lo reemplaza por `AV-{Pais}-{AAAA}-{ID con 6 dígitos}`. Indexar. |
| `PaisCodigo` | País | Elección: SV, GT, HN, NI, CR, P6 | Sí | App (derivado de la ubicación) | Indexar. Es la columna de filtro principal y de RLS. |
| `Ubicacion` | Ubicación | Búsqueda → `Cat_Ubicacion` (muestra `Title` = Código) | Sí | App | Agregar como campos adicionales `Nombre` y `Tipo`. |
| `UbicacionCodigo` | Código ubicación | Una línea de texto | Sí | App | Copia del código; sirve para delegación, índices y Power BI sin expandir la búsqueda. Indexar. |
| `TipoUbicacion` | Tipo de ubicación | Elección: CD, Tienda, Tránsito, Última milla | Sí | App | Se copia del catálogo. |
| `EtapaDeteccion` | Etapa de detección | Elección: Recepción proveedor, Almacenamiento CD, Picking / despacho CD, Transporte CD→tienda, Recepción tienda, Exhibición / bodega tienda, Entrega a cliente (last-mile), Devolución de cliente | Sí | App | Debe ser coherente con el tipo de ubicación (lo valida la app, ver abajo). |

### B. Clasificación

| Nombre interno | Nombre visible | Tipo | Obligatorio | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `TipoAveria` | Tipo de avería | Búsqueda → `Cat_TipoAveria` | Sí | App | |
| `Causa` | Causa | Búsqueda → `Cat_Causa` | Sí | App | |
| `TipoAveriaCodigo` | Código tipo de avería | Una línea de texto | Sí | App | Copia del código (TA01…). Power BI se relaciona con los catálogos por estos códigos sin expandir búsquedas. |
| `CausaCodigo` | Código causa | Una línea de texto | Sí | App | Copia del código (CA01…). |
| `ResponsableImputable` | Responsable imputable | Elección: Proveedor, Transportista, Operación CD, Tienda, Cliente, Aseguradora, Por determinar | Sí | App (precargado con `ResponsableDefault` de la causa) → editable por N2 | Es la base del reclamo y del indicador de averías por responsable. |
| `DisposicionPropuesta` | Disposición propuesta | Elección: Venta outlet, Venta como nuevo con reempaque, Reparación / reacondicionamiento, Reclamo a proveedor, Devolución a proveedor (RTV) / garantía, Reclamo a transportista, Reclamo a aseguradora, Donación, Destrucción, Por determinar | Sí | App (sugerida por catálogo) | |
| `DescripcionDano` | Descripción del daño | Varias líneas de texto (texto sin formato) | Sí | App | Mínimo 15 caracteres (app). |

### C. Producto y valorización

| Nombre interno | Nombre visible | Tipo | Obligatorio | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `SKU` | SKU | Una línea de texto | Sí | App (escáner o teclado) | Validación de columna: `=AND(LEN([SKU])>=4,LEN([SKU])<=20)`. Indexar. |
| `DescripcionProducto` | Descripción del producto | Una línea de texto | Sí | App | |
| `NumeroSerie` | N.º de serie | Una línea de texto | No | App | Obligatorio en la app cuando el tipo de avería es TA10 (garantía o RTV). |
| `Proveedor` | Proveedor | Una línea de texto | No | App / Control de Inventarios | Obligatorio para cerrar si el responsable es Proveedor. |
| `DocumentoOrigen` | Documento origen | Una línea de texto | No | App | N.º de recepción, traslado, factura o guía. Obligatorio en la app cuando la etapa es Recepción proveedor, Transporte CD→tienda o Entrega a cliente. |
| `Cantidad` | Cantidad | Número, 0 decimales | Sí | App | Validación de columna: `=AND([Cantidad]>0,[Cantidad]<=9999)`. |
| `Moneda` | Moneda | Elección: USD, GTQ, HNL, NIO, CRC | Sí | App (desde la ubicación) | |
| `CostoUnitarioLocal` | Costo unitario (moneda local) | Número, 2 decimales | No al crear, sí para enrutar | **Control de Inventarios** (paso de valorización) | Costo de Infor. **No lo digita el reportante.** Validación: `=OR(ISBLANK([CostoUnitarioLocal]),[CostoUnitarioLocal]>0)`. |
| `TipoCambioAplicado` | Tipo de cambio aplicado | Número, 6 decimales | No | Flujo | Unidades locales por 1 USD, del período vigente en `Cfg_TipoCambio`. |
| `CostoTotalLocal` | Costo total (local) | Calculada (número): `=[Cantidad]*[CostoUnitarioLocal]` | — | Sistema | |
| `CostoTotalUSD` | Costo total USD | Número, 2 decimales | No | **Flujo** | Lo escribe el flujo (no es una columna calculada) para poder indexarlo, filtrarlo de forma delegable y dejarlo congelado en la valorización. |
| `ValorRecuperableEstUSD` | Valor recuperable estimado USD | Número, 2 decimales | No | N2 / Control de Inventarios | Venta outlet, reclamo esperado, etc. **No interviene en los umbrales.** |
| `MontoRecuperadoUSD` | Monto recuperado real USD | Número, 2 decimales | No | Control de Inventarios | Se puede actualizar después del cierre (los reclamos tardan). |

### D. Flujo, aprobación y SLA

| Nombre interno | Nombre visible | Tipo | Obligatorio | Lo llena | Validación / notas |
|---|---|---|---|---|---|
| `Estado` | Estado | Elección (ver máquina de estados) | Sí, predeterminado `Borrador` | App / Flujo | Indexar. |
| `Tramo` | Tramo de aprobación | Elección: T1, T2, T3, T4 | No | Flujo | |
| `NivelesRequeridos` | Niveles requeridos | Número, 0 decimales | No | Flujo | 1–4. |
| `NivelActual` | Nivel actual | Número, 0 decimales | No | Flujo | 0 = valorización. |
| `VersionRegla` | Versión de regla | Una línea de texto | No | Flujo | Ej. `B-2026.1`. Se congela al enrutar, para auditar aunque cambien los parámetros. |
| `AlertaFraccionamiento` | Alerta de fraccionamiento | Sí/No, predeterminado No | No | Flujo | Sí cuando el acumulado del mismo SKU en la misma ubicación dentro de la ventana empuja a un tramo superior. |
| `AcumuladoVentanaUSD` | Acumulado en ventana USD | Número, 2 decimales | No | Flujo | |
| `AprobadorN1` … `AprobadorN4` | Aprobador N1 … N4 | Persona (una) | No | Flujo | Quien efectivamente respondió (puede ser el suplente). |
| `FechaN1` … `FechaN4` | Fecha N1 … N4 | Fecha y hora | No | Flujo | |
| `ComentarioAprobacion` | Comentarios de aprobación | Varias líneas de texto, **anexar cambios al texto existente** activado | No | Flujo | Requiere el control de versiones de la lista activado (lo está por defecto). |
| `JefeUbicacion` | Jefe de ubicación | Persona | No | Flujo | Resuelto desde `Cfg_Aprobadores`; lo usa la app para mostrar "mis pendientes". |
| `ControlInventarios` | Control de inventarios | Persona | No | Flujo | |
| `FechaDeteccion` | Fecha de detección | Solo fecha | Sí | App | Ver la validación de lista. |
| `FechaEnvio` | Fecha de envío | Fecha y hora | No | Flujo | Momento en que el estado pasa a Enviado. **Inicio de todos los SLA.** Indexar. |
| `FechaValorizacion` | Fecha de valorización | Fecha y hora | No | Flujo | |
| `FechaAprobacionFinal` | Fecha de aprobación / rechazo final | Fecha y hora | No | Flujo | |
| `FechaLimiteCierre` | Fecha límite de cierre | Fecha y hora | No | Flujo | `FechaEnvio + SLACierreDias` del tramo. Se congela. |
| `NumeroAjusteInfor` | N.º de ajuste Infor | Una línea de texto | No | Control de Inventarios (app) | **Obligatorio para cerrar un caso aprobado.** Validación: `=OR(ISBLANK([NumeroAjusteInfor]),LEN([NumeroAjusteInfor])>=4)`. |
| `EvidenciaDisposicion` | Evidencia de disposición | Una línea de texto | No | Control de Inventarios | N.º de acta de destrucción, reclamo, guía de RTV o factura outlet. |
| `FechaCierre` | Fecha de cierre | Fecha y hora | No | Flujo | |
| `CerradoATiempo` | Cerrado a tiempo | Sí/No | No | Flujo | `FechaCierre <= FechaLimiteCierre`. Se calcula al cerrar. |
| `ReporteTardio` | Reporte tardío | Sí/No | No | Flujo | Detección → envío mayor que `MaxDiasDeteccionAReporte`. |
| `MotivoRechazo` | Motivo de rechazo / devolución | Varias líneas de texto | No | Flujo | |
| `Attachments` | Datos adjuntos (fotos) | Sistema | Mínimo según `FotosMinimas` del tipo | App | Fotos del producto, la etiqueta del SKU o la serie, y el empaque. |
| `Created` / `Author` | Creado / Creado por | Sistema | — | Sistema | `Author` = reportante. |
| `ReportanteEmail` | Correo del reportante | Una línea de texto | Sí | App (`User().Email`) | Copia en texto para Power BI (concentración por reportante) y para la segregación en el flujo, sin expandir columnas Persona. |

### Máquina de estados (`Estado`)

```
Borrador ──(app: Enviar)──► Enviado ──(AV-01)──► Pendiente N1
Pendiente N1 ──aprobado──► Pendiente valorización ──(Control Inv. ingresa costo)──► Valorizado
Pendiente N1 ──rechazado──► Rechazado (fin)
Pendiente N1 ──devuelto──► Devuelto para corrección ──(app: reenviar)──► Enviado
Valorizado ──(AV-02)──► Pendiente ajuste Infor                (si NivelesRequeridos = 1)
Valorizado ──(AV-02)──► Pendiente N2 ──► N3 ──► N4 ──► Pendiente ajuste Infor   (según el tramo)
Cualquier Pendiente Nx ──rechazado──► Rechazado (fin)
Pendiente ajuste Infor ──(Control Inv. ingresa N.º de ajuste y evidencia)──► Cerrado (AV-03)
Borrador / Devuelto ──(reportante)──► Anulado (fin)
```

Valores de la elección `Estado`: Borrador, Enviado, Pendiente N1, Devuelto para corrección, Pendiente valorización, Valorizado, Pendiente N2, Pendiente N3, Pendiente N4, Pendiente ajuste Infor, Cerrado, Rechazado, Anulado.

**Por qué N1 va antes que la valorización:** el jefe de la ubicación valida lo físico (que la avería existe y las fotos corresponden) y eso no depende del costo. Control de Inventarios valoriza con el costo de Infor solo los casos que sobreviven a N1, y es la misma persona que después registra el ajuste. Así el costo, que decide el tramo, no lo digita quien reporta.

### Validación de lista (Configuración de la lista → Validación)

Una sola fórmula (SharePoint permite una por lista):

```
=AND(
  [FechaDeteccion]<=TODAY(),
  [FechaDeteccion]>=DATE(2026,1,1),
  OR([Estado]<>"Cerrado", NOT(ISBLANK([NumeroAjusteInfor]))),
  OR([Estado]<>"Valorizado", NOT(ISBLANK([CostoUnitarioLocal])))
)
```

Mensaje: `Revisá: la fecha de detección no puede ser futura; para cerrar se requiere el N.º de ajuste Infor; para valorizar se requiere el costo unitario.`

> SharePoint exige que la fórmula vaya en una sola línea; los saltos están solo para leerla. Ojo con `TODAY()`: se evalúa al guardar, así que un caso editado días después sigue siendo válido mientras la fecha no sea futura.

### Validaciones que van en Power Apps (no las puede hacer SharePoint)

- Fotos ≥ `FotosMinimas` del tipo de avería.
- Coherencia entre ubicación y etapa: Tienda → {Recepción tienda, Exhibición / bodega tienda, Devolución de cliente}; CD → {Recepción proveedor, Almacenamiento CD, Picking / despacho CD}; Tránsito → {Transporte CD→tienda}; Última milla → {Entrega a cliente (last-mile)}.
- `NumeroSerie` obligatorio cuando el tipo es TA10; `DocumentoOrigen` obligatorio según la etapa.
- Aviso de posible duplicado: el mismo SKU en la misma ubicación en las últimas 72 h (`Filter` sobre `UbicacionCodigo`, `SKU` y `Created`, todos delegables).
- El reportante solo ve y edita sus casos en estado Borrador o Devuelto. Las pantallas de aprobación y valorización filtran por `JefeUbicacion` y `ControlInventarios`.

### Índices (Configuración de la lista → Columnas indizadas)

Crearlos **antes** de llegar a 5 000 ítems (después SharePoint no deja crearlos en listas grandes): `PaisCodigo`, `Estado`, `UbicacionCodigo`, `FechaEnvio`, `SKU`, `Title`, `Created`. Con unas 1 500–2 800 averías al mes, la lista pasa los 5 000 ítems en 2 o 3 meses.

### Vistas sugeridas

- `Pendientes por país`: Estado ≠ Cerrado, Rechazado ni Anulado, agrupada por `PaisCodigo` y luego `Estado`.
- `Pendiente ajuste Infor`: para Control de Inventarios, ordenada por `FechaAprobacionFinal` ascendente.
- `Vencidas`: abiertas con `FechaLimiteCierre` < [Hoy]. Se filtra en la vista; las vistas sí admiten [Hoy].

---

## Listas de soporte

Todas se crean con **Nueva lista → Desde CSV** usando los archivos de `catalogos/` y `config/`. Después se ajustan los tipos: SharePoint importa todo como texto, así que hay que convertir Sí/No, números y personas.

| Lista | Archivo | Columnas clave y tipo | Quién la mantiene |
|---|---|---|---|
| `Cat_TipoAveria` | `catalogos/tipo_averia.csv` | `Title`=Codigo; Nombre (texto); Categoria (elección); RequiereFoto (Sí/No); FotosMinimas (número); RequiereDiagnosticoTecnico (Sí/No); DisposicionSugerida (texto); Activo (Sí/No); Orden (número) | Logística regional |
| `Cat_Causa` | `catalogos/causa.csv` | `Title`=Codigo; Nombre; EtapaTipica; ResponsableDefault (elección); AplicaReclamo (Sí/No); DisposicionSugerida; Activo; Orden | Logística regional |
| `Cat_Ubicacion` | `catalogos/ubicacion.csv` | `Title`=Codigo (indexado); Nombre; Tipo (elección); PaisCodigo (elección, indexado); CDAbastecedor; CodigoInfor; Moneda; Activo; EsEjemplo | Control de Inventarios por país |
| `Cfg_Umbrales` | `config/umbrales_aprobacion.csv` | `Title`=Version; PaisCodigo (`*` = todos); Nivel; MontoDesdeUSD y MontoHastaUSD (número); NivelesRequeridos; RolN1–RolN4; SLAAprobacionHorasPorNivel; SLACierreDias; VigenteDesde y VigenteHasta (fecha); Activo | Solo Logística regional |
| `Cfg_Parametros` | `config/parametros_generales.csv` | `Title`=Clave; Valor (texto); Descripcion | Solo Logística regional |
| `Cfg_Aprobadores` | `config/aprobadores_plantilla.csv` | PaisCodigo; UbicacionCodigo (`*` = todas); Rol (elección); Aprobador (**Persona**); Suplente (**Persona**); Activo | Gerente de logística de cada país |
| `Cfg_TipoCambio` | `config/tipo_cambio.csv` | `Title`=Periodo (AAAA-MM); Moneda; UnidadesPorUSD (número, 6 decimales); Fuente; Activo | Finanzas país / Logística regional, mensual |
| `Cfg_AccesoBI` | `config/acceso_bi_plantilla.csv` | Email (texto); PaisCodigo (texto, `*` = todos) | Logística regional |
| `Averias_Historial` | (vacía) | `Title`=Folio; AveriaID (número, indexado); Accion (elección: Enviado, Aprobado, Rechazado, Devuelto, Valorizado, Recordatorio, Escalado a suplente, Cerrado, Anulado); Nivel (número); Actor (Persona); FechaInicio y FechaFin (fecha y hora); DuracionHoras (número); Comentario (varias líneas) | Solo la escriben los flujos |

**Al importar `Cfg_Aprobadores` desde CSV**, las columnas de correo quedan como texto. Creá a mano las columnas Persona `Aprobador` y `Suplente` y cargalas en la vista de cuadrícula pegando los correos: SharePoint resuelve a la persona.

**Maestro de tiendas:** `ubicacion.csv` trae los CD, una ubicación virtual de tránsito y una de última milla por país, más filas de ejemplo de tiendas (`EsEjemplo = Sí`). Reemplazá las tiendas con un export del maestro de tiendas de Infor (código, nombre, CD que la abastece y código Infor) y borrá las filas de ejemplo antes de salir a producción.
