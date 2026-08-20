# Fútbol — LaLiga, Copa del Rey y Champions League

Página web autocontenida (`index.html`, sin dependencias ni build), **en castellano**, que reúne tres
competiciones en un mismo sitio. Se cambia de competición con las pestañas superiores y cada una tiene
su propio color de acento (LaLiga en rojo, Copa del Rey en dorado, Champions en azul).

## Qué muestra, en cada competición

- **Partidos**: agrupados por jornada o eliminatoria, con marcador, fecha, sede y estado. Se filtran por
  equipo, por estado (jugados / por jugar) y por ronda.
- **Detalle de cada partido** (al pulsar sobre él):
  - **Figura del partido**: el jugador más decisivo del encuentro (ver nota abajo).
  - Goles (con penalti y gol en propia puerta señalados) y tarjetas, minuto a minuto.
  - **Estadísticas de los dos equipos**: remates, posesión, córners, faltas, fueras de juego… con barras
    comparativas.
- **Equipos**: clasificación completa en LaLiga (PJ, G, E, P, GF, GC, DG, Pts y racha de forma) y, en las
  competiciones por eliminatorias, una tabla equivalente de rendimiento en el torneo.
- **Goleadores** y **Asistentes**: rankings con barra proporcional y podio.
- **Panel de cifras**: partidos jugados, goles, media de goles por partido y número de equipos.

Tema **oscuro por defecto**, con botón para cambiar a claro (se recuerda la preferencia).

## Sobre el "mejor jugador del partido"

Ninguna de las fuentes disponibles publica el **premio oficial** al mejor jugador del partido, ni la UEFA
en sus datos abiertos ni los proveedores usados para LaLiga y Copa del Rey. Para no presentar como
oficial algo que no lo es, la app calcula una **"figura del partido"** con los datos reales del encuentro:

```
puntuación = goles × 2 + asistencias × 1
```

Aparece siempre etiquetada como *calculada*. Si en el futuro se conecta una fuente que publique el premio
oficial, se puede sustituir sin tocar el resto de la app.

## Fuentes de datos y cobertura

| Competición | Fuente | Cobertura |
|---|---|---|
| Champions League | API oficial de la **UEFA** | Completa: partidos, goles con nombre, asistencias y estadísticas oficiales por partido |
| LaLiga | **TheSportsDB** | Resultados, clasificación y estadísticas de equipo completos; el detalle por partido viene recortado por el proveedor gratuito, así que goleadores y asistentes pueden estar incompletos |
| Copa del Rey | **TheSportsDB** | Igual que LaLiga |

Esa limitación se indica dentro de la propia página, para que no se confunda un dato parcial con uno completo.

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

El script es **incremental**: reutiliza lo ya descargado y solo vuelve a pedir los días recientes o los
partidos sin detalle, de modo que cada ejecución programada es rápida.

## Cómo usarla

Abre `index.html` en cualquier navegador, o sirve la carpeta (`python3 -m http.server`) y entra a
`http://localhost:8000`. No requiere instalación ni clave de API propia.
