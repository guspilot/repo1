# 07 — Plan de piloto: El Salvador

## Decisiones de partida

- **País piloto: El Salvador.** Tiene el CD y la gerencia regional en el mismo lugar, opera en USD (sin riesgo de tipo de cambio en el piloto) y el personal de tienda tiene licencias M365.
- **El piloto va en dos fases**, porque una sola fase de 4 semanas con 10 tiendas **no alcanza para calibrar la recurrencia**. Con ~2 averías por tienda al mes, 10 tiendas generan unos 20 casos de tienda en 4 semanas, y R3a necesita el λ de todo el país y R1/R2 necesitan historia por SKU y por proveedor.

| Fase | Alcance | Duración | Qué valida | `RecurrenciaModo` |
|---|---|---|---|---|
| **1 — Proceso** | CD SV + 10 tiendas | 4 semanas | Que el flujo funcione de punta a punta: usabilidad en el teléfono, SLA, carga real de CI y de Operaciones, y calidad de la clasificación | Observar |
| **2 — Escala** | CD SV + **todas** las tiendas SV | 4 semanas | Volumen real, carga por aprobador y datos suficientes para calibrar λ, `FactorTamano` y la recurrencia con el simulacro | Observar |
| **3 — Aplicar** | Todo SV | En adelante | La recurrencia ya cambia el nivel. Es la operación normal | **Aplicar** |

## Calendario recomendado

**No arrancar en temporada alta.** Lanzar un proceso nuevo en tiendas entre Black Friday (27 de noviembre) y fin de año pone el aprendizaje justo en el pico de volumen y de rotación de personal, y es la forma más rápida de que la gente lo rechace. Noviembre se usa para construir y probar.

| Semanas | Fechas | Hito |
|---|---|---|
| S1 | 2–6 nov 2026 | Sitio, listas, catálogos, configuración y aprobadores cargados |
| S2–S3 | 9–20 nov | Flujos AV-01 a AV-05 y app; los 20 casos de prueba de los flujos y las pruebas de la app (05 y 06) |
| S4 | 23–27 nov | UAT con usuarios reales de 2 tiendas y del CD, con casos ficticios |
| S5–S6 | 30 nov–11 dic | Ajustes del UAT; tablero de Power BI con los datos de prueba; materiales de capacitación |
| — | 14 dic–8 ene 2027 | **Congelamiento por temporada alta.** El proceso actual sigue igual |
| S7 | 11–15 ene 2027 | Capacitación (Fase 1) y **arranque de la Fase 1** el lunes 11 |
| S7–S10 | 11 ene–5 feb | Fase 1 |
| S11 | 8 feb | Decisión de avance a la Fase 2. Capacitación del resto de las tiendas SV (virtual, 45 min) |
| S11–S14 | 8 feb–5 mar | Fase 2 |
| S15 | 8–12 mar | Simulacro con los datos reales, recalibración y paso a **Aplicar** |
| S16–S17 | 15–26 mar | Estabilización y **decisión de despliegue regional** |

> **Costo de esperar a enero:** la política está vigente desde el 2026/05/01 y exige el workflow digital [7.1, 8.2.4], así que cada mes sin él es un mes de incumplimiento formal. Recomiendo informárselo al BPO (COO) junto con este calendario, para que el congelamiento de diciembre quede como decisión explícita y no como atraso.

## Selección de las 10 tiendas de la Fase 1

Los criterios buscan exponer el proceso a todos sus caminos, no elegir las tiendas "fáciles":

| Criterio | Cantidad | Por qué |
|---|---|---|
| Tiendas grandes (`FactorTamano` ≥ 1.5) | 2 | Volumen y casos con varias líneas |
| Tiendas medianas | 5 | El caso típico |
| Tiendas chicas | 3 | Verificar que el proceso no sea demasiado pesado para equipos pequeños |
| Al menos 1 con entrega a domicilio | (incluida) | Probar última milla y la regla de la tienda vendedora (D7) |
| Al menos 2 con historial alto de averías o diferencias de inventario | (incluidas) | Probar la recurrencia y la reacción del Gerente de Tienda |
| Todas a menos de 1 h del CD | — | Soporte presencial en la primera semana |

El CD SV entra completo desde la Fase 1. Probablemente es el CDD Nejapa, donde **también corre el piloto de tiempos en muelle**. Conviene que los dos pilotos no le pidan cosas nuevas al mismo equipo de recepción la misma semana. Recomiendo coordinar la capacitación de averías del CD para que no coincida con un hito del piloto de muelles.

## Roles del piloto

| Rol | Quién (a definir) | Dedicación en la Fase 1 |
|---|---|---|
| Dueño del piloto | Gerente Corporativo de Logística ULA | Revisión semanal (30 min) |
| Líder operativo SV | Gerente de Logística SV | Diaria (15 min) + revisión semanal |
| Constructor (Power Platform) | Persona de Logística regional con experiencia en Power Apps y Power Automate | S1–S6 al 100 %; Fase 1 al 30 % para ajustes |
| CI SV — valorizador | Analista de CI | ~40 min/día (estimado) |
| CI SV — aprobador N3 | Jefe de CI SV | ~20–35 min/día (estimado) |
| Operaciones local SV | Gerente de Operaciones / zona | ~30–50 min/día (estimado) |
| Gerente de Producto SV | (uno por categoría o uno general) | Por evento, SLA 72 h |
| ST | Coordinador de ServiTotal / Servitech SV | Por evento |
| Embajador por tienda | El Gerente de Tienda o el subgerente | Es el primer nivel de soporte para su equipo |

**Antes de arrancar:** los aprobadores y suplentes de los 10 roles tienen que estar cargados en `Cfg_Aprobadores`. **Ningún rol sin suplente.**

## Datos que se necesitan antes de la S1

| Dato | Fuente | Para qué |
|---|---|---|
| Maestro de tiendas SV (código, nombre, código Infor) | Infor | `Cat_Ubicacion` |
| Ventas por tienda, últimos 3 meses | BI de ventas | `FactorTamano` |
| **Histórico de 12 meses de ajustes por avería en SV** (fecha, tienda o CD, SKU, proveedor, cantidad, costo) | Infor | **Calibrar la recurrencia antes del piloto.** Con este histórico corro el simulacro sobre datos reales y la Fase 1 arranca con λ, k y la carga esperada ya medidos, no supuestos |
| Códigos de motivo de movimiento Infor por disposición | CI SV | El aviso de ejecución de AV-03 |
| Correos de aprobadores y suplentes | Gerente de Logística SV | `Cfg_Aprobadores` |

## Capacitación

| Público | Formato | Duración | Contenido |
|---|---|---|---|
| Personal de tienda y CD (reportantes) | Presencial en la tienda, en el teléfono de cada uno | 30 min | Reportar en menos de 3 minutos, fotos, sin serie, plazo de 24 h y consolidación física |
| Gerentes de Tienda y de Logística CD | Virtual | 45 min | Bandeja, aprobación en Teams, definir la disposición y por qué no se aprueba por WhatsApp ni por correo [8.2.4] |
| CI, Operaciones, Gerente de Producto, Compras, ST | Virtual por rol | 45 min | Su pantalla, su SLA, la matriz y por qué les llega cada caso (`MotivoNivel`) |
| Todos | Ficha de una página en PDF + video de 3 min | — | Para consultar después |

## Indicadores del piloto y criterios de avance

Se revisan cada viernes en el tablero, con el filtro SV.

| Indicador | Meta para pasar a la Fase 2 | Meta para el despliegue regional |
|---|---|---|
| % de reportes dentro de 24 h [8.2.1] | ≥ 80 % | ≥ 90 % |
| % de aprobaciones dentro de 48 h [8.2.2] | ≥ 85 % | ≥ 90 % |
| Mediana de horas de valorización (CI) | ≤ 24 h | ≤ 12 h |
| % de autorizaciones de descuento dentro de 72 h [7.6] | ≥ 80 % | ≥ 90 % |
| % de casos con clasificación corregida por CI (origen o causa) | ≤ 25 % | ≤ 10 % |
| % de casos devueltos por información incompleta | ≤ 15 % | ≤ 8 % |
| % de cumplimiento del SLA de cierre E2E | Se mide; sin meta en la Fase 1 | ≥ 80 % |
| Casos N3 por día hábil para CI | Se mide y se compara con el escenario base (~3.5) | ≤ 6, o un analista dedicado asignado |
| Averías gestionadas fuera del workflow (correo o WhatsApp) detectadas | 0 casos de aprobación por fuera | 0 |
| Fallas de flujo (ejecuciones con error) | ≤ 2 % | ≤ 0.5 % |
| Tiempo de reporte en el teléfono (medido en la capacitación) | ≤ 5 min | ≤ 3 min |

**Regla de avance:** se pasa de fase si se cumplen todas las metas **o** si cada meta incumplida tiene una causa identificada y una corrección en curso. No se avanza con fallas de flujo por encima del 2 %, porque eso es un problema técnico y no de adopción.

## Riesgos del piloto

| Riesgo | Señal temprana | Mitigación |
|---|---|---|
| El personal sigue reportando por WhatsApp | Averías que aparecen en un conteo sin ticket | El Gerente de Tienda no acepta ninguna avería sin folio; auditorías sorpresa de CI [9.3] |
| CI se satura con valorización + N3 | Mediana de valorización > 24 h en la semana 2 | Separar valorizador y aprobador desde el día 1; si sigue, subir `RecTienda_Alfa` o asignar un analista |
| Operaciones local es una sola persona | Mediana de aprobación N2 > 24 h | Suplente formal; si sigue, dividir por zona en `Cfg_Aprobadores` |
| Señal débil en bodegas de tienda | Borradores que no se envían | Las líneas se guardan en el teléfono (06); enviar desde el piso de venta |
| Clasificación inconsistente | % corregido por CI > 25 % | Ajustar las definiciones en el catálogo y repasar en la reunión semanal con ejemplos reales |
| Límite de acciones de Power Automate | Ejecuciones "limitadas" | En SV no debería pasar (~12–23 casos por día); en el despliegue regional, repartir dueños (05) |
