# Fútbol — LaLiga, Copa del Rey y Champions League

Página web autocontenida (`index.html`, sin dependencias ni build), **en castellano**, que reúne tres
competiciones en un mismo sitio. Se cambia de competición con las pestañas superiores y cada una tiene
su propio color de acento (LaLiga en rojo, Copa del Rey en dorado, Champions en azul).

## Qué muestra, en cada competición

- **Partidos**: agrupados por día en liga y por eliminatoria en las copas, con marcador, fecha, sede y
  estado. Se filtran por equipo, por estado (jugados / por jugar) y por ronda.
- **Detalle de cada partido** (al pulsar sobre él):
  - **Figura del partido**: el jugador más decisivo del encuentro (ver nota abajo).
  - Goles (con penalti y gol en propia puerta señalados) y tarjetas, minuto a minuto.
  - **Estadísticas de los dos equipos**: remates, posesión, córners, faltas, fueras de juego… con barras
    comparativas.
- **Equipos**: clasificación completa en LaLiga (PJ, G, E, P, GF, GC, DG, Pts y racha de forma) y, en las
  competiciones por eliminatorias, una tabla equivalente de rendimiento en el torneo.
- **Goleadores** y **Asistentes**: rankings con barra proporcional y podio.
- **Pronóstico** en los partidos por jugar: probabilidad de victoria local, empate o victoria visitante.
- **Panel de cifras**: partidos jugados, goles, media de goles por partido y número de equipos.

Tema **oscuro por defecto**, con botón para cambiar a claro (se recuerda la preferencia).

## Sobre el "mejor jugador del partido"

La fuente no publica el **premio oficial** al mejor jugador del partido. Para no presentar como oficial
algo que no lo es, la app calcula una **"figura del partido"** con los datos reales del encuentro:

```
puntuación = goles × 2 + asistencias × 1
```

Aparece siempre etiquetada como *calculada*. Si en el futuro se conecta una fuente que publique el premio
oficial, se puede sustituir sin tocar el resto de la app.

## El pronóstico

En cada partido aún no disputado se muestra una barra con la probabilidad de los tres resultados
(**1-X-2**). Sale de un modelo de Poisson que estima la fuerza atacante y defensiva de cada equipo a
partir de los resultados de la propia competición y tiene en cuenta la **ventaja de jugar en casa**
(se calculan por separado las medias de goles de local y de visitante).

A principio de temporada no hay datos suficientes para distinguir a un equipo de otro —con tres
jornadas jugadas todos los partidos saldrían casi 50-50—, así que el modelo se apoya además en los
resultados de la **temporada anterior** con menos peso (cuentan un 35 %). Ese apoyo se retira solo en
cuanto la competición supera los 60 partidos jugados. Los resultados anteriores se descargan sin
detalle (solo marcadores), así que salen prácticamente gratis.

Las probabilidades se refieren al resultado al final del **tiempo reglamentario**: en una eliminatoria,
un empate significa que el partido llegaría a la prórroga, no que la eliminatoria acabe en tablas. Es
una estimación, no una apuesta.

## Fuente de datos y cobertura

Todo sale de la **API pública de ESPN** (la misma que alimenta su web; no hace falta clave ni
cabeceras especiales), en una sola tubería para las tres competiciones:

| Dato | Cobertura |
|---|---|
| Partidos, marcadores, sede | Completos, incluidas las rondas previas |
| Goles con goleador y asistente | Completos |
| Tarjetas | Completas |
| Estadísticas de equipo por partido | Posesión, remates, remates a puerta, córners, faltas, fueras de juego, paradas y pases |
| Goleadores y asistentes | Completos |

Los goleadores y asistentes salen de las **estadísticas por jugador** de cada partido y, cuando ESPN no
las publica (algo habitual en rondas modestas de copa), se deducen de los propios goles del encuentro,
que sí traen goleador y asistente. Así los rankings no se quedan cojos.

Comprobación de contraste: en LaLiga los goles atribuidos cuadran exactamente con los goles marcados
(17 de 17); en Champions se cubre el 98 %. Lo que falta son goles en propia puerta —que no se atribuyen
a ningún goleador, como debe ser— y algún partido suelto sin detalle publicado.

### Por qué no Flashscore

Se valoró. Su `robots.txt` prohíbe expresamente el acceso automatizado a las rutas donde viven sus
feeds de datos (`/x/`, `/clasificacion/`) y sus condiciones no permiten reutilizar el contenido, que
aquí además se republicaría en una web pública. ESPN ofrece los mismos datos —o más— con una API
pensada para ser consumida, así que no hacía falta.

## Temporadas: se eligen solas

Ninguna temporada está fijada en el código. En cada ejecución el recolector calcula la temporada
europea en curso (arranca en julio) y comprueba si la fuente ya publica partidos:

- Si los hay, usa esa temporada.
- Si todavía no ha empezado —el caso típico de la **Copa del Rey**, que arranca a finales de octubre—,
  muestra la **última edición disputada** y la etiqueta como tal, tanto en la pestaña de la competición
  como en un aviso dentro de la página.

En cuanto la nueva edición publica su primer partido, la app pasa a ella automáticamente (como muy tarde
en la siguiente ejecución programada, ~30 min), sin tocar el código.

Durante ese relevo la edición anterior no se pierde: mientras la nueva copa lleve menos de 10 partidos
jugados se descargan **las dos**, y aparece un selector de edición para moverse entre ellas. Así la
página nunca se queda casi vacía justo después del cambio. Cuando la nueva edición ya está en marcha,
la antigua deja de descargarse. En liga no se aplica, porque una temporada empieza con todos los equipos
y no existe ese hueco.

## Actualización automática

Los datos **no se descargan desde el navegador** (eso falla en navegadores que bloquean peticiones entre
sitios, como Brave con sus escudos). En su lugar:

1. `.github/workflows/futbol-data.yml` ejecuta `scripts/fetch_futbol.py` cada ~30 minutos en GitHub Actions.
2. El script descarga los datos y guarda `Futbol/data.json` en el repositorio.
3. La web lee ese `data.json` **desde su mismo origen**, que ningún navegador bloquea, y además lleva una
   instantánea incorporada para funcionar aunque no haya red.

El script es **incremental**: el detalle de un partido terminado no cambia, así que solo se piden los
partidos nuevos (con un tope por ejecución para que un run no se eternice; el resto entra en el
siguiente). Además las consultas de calendario van por rangos de fechas, no día a día.

## Cómo usarla

Abre `index.html` en cualquier navegador, o sirve la carpeta (`python3 -m http.server`) y entra a
`http://localhost:8000`. No requiere instalación ni clave de API propia.
