# Mundial 2026 — Seguimiento en vivo

Página web autocontenida (`index.html`, sin dependencias ni build) que muestra todos los
partidos del Mundial 2026 — jugados, en vivo y por jugar —, goles y goleadores con minuto y
asistencia, tarjetas, y tabla de posiciones por grupo calculada en tiempo real. Se actualiza
sola cada 90 segundos mientras la tengas abierta en el navegador (o al pulsar "Actualizar ahora").

## Cómo usarla

Solo abre `index.html` en cualquier navegador (doble clic, o `python3 -m http.server` en esta
carpeta y entrar a `http://localhost:8000`). No requiere instalación, servidor ni API key propia
para empezar a funcionar.

## Fuente de datos

Usa la API pública de [TheSportsDB](https://www.thesportsdb.com) con su clave de prueba gratuita.
Para evitar el límite de "5 resultados por consulta" de esa clave, la app recorre día por día todo
el calendario del torneo (11 jun – 19 jul 2026) y combina los resultados, en vez de pedir el
calendario completo de una sola vez.

**Cobertura y limitaciones:**
- Con la clave gratuita puede haber partidos, goles o eventos no disponibles todavía en la base de
  datos de TheSportsDB, sobre todo justo después de terminar un partido.
- La clave está en `API_KEY` al inicio del `<script>` de `index.html`. Si más adelante consigues una
  clave de pago (TheSportsDB Patreon, desde 3 USD/mes) solo tienes que reemplazar ese valor — el
  resto del código no cambia y la cobertura pasa a ser completa.
- Los datos son "mejor esfuerzo": para resultados oficiales, contrasta con FIFA.com.

## Estructura

Todo vive en un único archivo (`index.html`, HTML + CSS + JS vanilla, sin frameworks) para que sea
fácil de abrir, copiar o desplegar en cualquier hosting estático (GitHub Pages, Netlify, etc.).
