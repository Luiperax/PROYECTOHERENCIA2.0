# Mundial 2026 — Seguimiento en directo

Página web autocontenida (`index.html`, sin dependencias ni build), **100 % en castellano**, que
muestra todos los partidos del Mundial 2026 — jugados, en directo y por jugar —, con goles (autor,
minuto y asistente), tarjetas, tabla de posiciones por grupo calculada en tiempo real, y clasificaciones
de **goleadores** y **asistentes**. Se actualiza sola cada 90 segundos mientras la tengas abierta en el
navegador (o al pulsar el botón ↻).

## Características

- **Datos oficiales de la FIFA**, con nombres de selecciones en español y bandera de cada país.
- **Panel de cifras**: partidos jugados, goles marcados, media de goles por partido y nº de selecciones.
- **Partidos** (los 104) agrupados por día, con marcador, sede y estado (los partidos en directo se
  resaltan en rojo). Toca un partido para ver su detalle: goles con asistencia y tarjetas minuto a minuto,
  más la **“figura del partido” calculada** (ver nota abajo).
- **Grupos**: los 12 grupos con su clasificación (PJ, G, E, P, GF, GC, DG, Pts), racha de forma y
  puestos de clasificación resaltados.
- **Goleadores** y **Asistentes**: rankings con barra proporcional y podio (oro/plata/bronce).
- **Pronóstico** en los partidos por jugar: probabilidad de que cada selección gane/avance, con un
  modelo estadístico (Poisson de ataque/defensa) calculado a partir de los resultados del torneo.
- **Instantánea incorporada**: la app trae datos reales precargados, así se ve poblada al instante y
  funciona aunque no haya red; cuando hay conexión, se actualiza por encima de esa base.
- **Tema oscuro por defecto** con botón para cambiar a claro (la preferencia se recuerda).

## Actualización automática (importante)

Para que los datos se actualicen **en cualquier navegador** —incluidos los que bloquean peticiones
entre sitios, como Brave con sus escudos—, la actualización **no depende del navegador**: una tarea
programada de GitHub Actions (`.github/workflows/mundial-data.yml`) ejecuta `scripts/fetch_data.py`
cada ~15 minutos, descarga los datos de la FIFA y guarda `data.json` en el propio repositorio. La web
lee ese `data.json` **desde su mismo origen** (nunca bloqueado) y, como respaldo, intenta también la
API de la FIFA en directo, y por último la instantánea incorporada.

### Sobre el "mejor jugador del partido"

El premio oficial al mejor jugador del partido **no lo publican ni la FIFA (en sus datos abiertos) ni
periódicos como AS** (que solo ofrecen titulares, no datos de partido reutilizables). Para no inventarlo,
en su lugar se muestra una **“figura del partido” calculada** a partir de los goles y asistencias de cada
jugador en ese encuentro, claramente etiquetada como calculada (no es el premio oficial).

## Cómo usarla

Abre `index.html` en cualquier navegador (doble clic, o `python3 -m http.server` en esta carpeta y
entra a `http://localhost:8000`). No requiere instalación, servidor ni clave de API propia.

## Fuente de datos

Usa la **API pública oficial de la FIFA** (`api.fifa.com`, competición `17`, temporada `285023` = Mundial
2026), que admite peticiones desde el navegador (CORS abierto). La app pide el calendario completo (104
partidos) en una sola llamada y el detalle de cada partido (goles, asistencias, tarjetas) bajo demanda.

**Cobertura y limitaciones:**
- Es una API no documentada de la FIFA; su estructura podría cambiar en el futuro.
- Justo al terminar un partido, algún gol o dato puede tardar unos minutos en reflejarse.
- Los identificadores de competición/temporada están al inicio del `<script>` de `index.html`
  (`CID` y `SID`), por si hubiera que ajustarlos.

## Estructura

Todo vive en un único archivo (`index.html`, HTML + CSS + JS vanilla, sin frameworks) para que sea
fácil de abrir, copiar o desplegar en cualquier hosting estático (GitHub Pages, Netlify, etc.).
