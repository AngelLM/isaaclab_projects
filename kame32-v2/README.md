# Kame32 — proyecto unificado

Kame32 es un robot cuadrúpedo pequeño (unos 15 cm, tipo MiniKame) con una ESP32 y ocho servos MG90s. El objetivo del proyecto es que aprenda a caminar por aprendizaje por refuerzo en Isaac Lab y llevar esa política al robot real.

Esta carpeta reúne todo lo que se hizo entre noviembre de 2025 y julio de 2026, que estaba repartido por el ordenador, y es el punto de partida para rehacer el entrenamiento desde cero. Las carpetas originales no se han tocado: todo lo de aquí es una copia.

## Qué hay en cada carpeta

| Carpeta | Contenido | Origen |
|---|---|---|
| `hardware/kame32-JavierIH/` | **Submódulo de git** con el repositorio original de Kame32, sin modificar: piezas en FreeCAD/STEP/STL, placa en KiCad y firmware original (marcha por osciladores + joystick web). Tras clonar: `git submodule update --init` | [github.com/JavierIH/kame32](https://github.com/JavierIH/kame32) |
| `hardware/cad-extra/` | Piezas de CAD añadidas después de descargar el diseño (STEP sueltos, variantes `mg2` de bracket y pata de abril de 2026, ensamblaje completo en STL) | `~/Desktop/kame32-main/3d/` (lo que no venía en el zip) |
| `modelo/blender/` | El robot montado en Blender, desde donde se exportaron las piezas bien posicionadas y escaladas | `~/Desktop/kame32-main/kame32.blend` |
| `modelo/stl/` | Las piezas exportadas desde Blender (Body, Bracket, Leg, Foot de cada pata) | `~/Desktop/kame32-main/NewSTL/` |
| `modelo/usd/kame32.usd` | **El modelo definitivo del robot para la simulación**, con juntas, masas y colisiones | `~/kame/usd/kamerotated.usd` (idéntico a `kame32/assets/kame32.usd`) |
| `firmware/` | Firmware de PlatformIO que ejecuta la política entrenada en la ESP32. Solo lleva lo propio (red, calibración de tus servos, calibración ampliada); el resto lo toma del submódulo. Compila: `pio run -e policy` | `~/Desktop/kame32-rl/` |
| `entrenamiento/` | **El proyecto de entrenamiento nuevo**, que se construye desde cero | — |
| `archivo/intento1-direct-rslrl/` | Primer intento de entrenamiento (marzo–abril 2026), abandonado | `~/kame/` |
| `archivo/intento2-manager-skrl/` | Segundo intento (mayo–junio 2026), que sí consiguió caminar en simulación, con sus tres mejores políticas | `isaaclab_projects/kame32/` |
| `archivo/usd-iteraciones/` | Las versiones intermedias del USD hasta llegar al definitivo (no se suben a git) | `~/kame/usd/`, `~/Desktop/kame32-main/` |
| `docs/` | La documentación del proyecto completo | — |

## Créditos y licencias

Kame32 es un diseño de **JavierIH**: <https://github.com/JavierIH/kame32>. Este proyecto parte de su trabajo, que se incluye como submódulo sin modificar en `hardware/kame32-JavierIH/`. Su repositorio publica el código bajo **GPL-3.0** y el diseño del robot bajo **CC BY-SA 4.0**.

Hay partes de esta carpeta derivadas de su trabajo, que mantienen esas mismas licencias:

- `firmware/`: parte del firmware original (librerías `Kame` y `Octosnake`, joystick web y herramienta de calibración), con la calibración de los servos de este robot y el control por política añadidos. GPL-3.0.
- `modelo/` y `hardware/cad-extra/`: piezas reexportadas y modelo de simulación hechos a partir de su diseño. CC BY-SA 4.0.

## Documentación

- [`docs/00-historia.md`](docs/00-historia.md): qué se hizo, en qué orden y por qué.
- [`docs/01-hardware.md`](docs/01-hardware.md): el robot real, los pines de la ESP32 y cómo conectar la IMU.
- [`docs/02-modelo-usd.md`](docs/02-modelo-usd.md): cómo está construido el modelo de simulación y qué le falta.
- [`docs/03-lecciones-aprendidas.md`](docs/03-lecciones-aprendidas.md): lo que salió mal en los intentos anteriores, para no repetirlo.

La documentación detallada de cada intento y del firmware sigue dentro de su carpeta (`archivo/intento2-manager-skrl/codigo/docs/` y `firmware/docs/`).

## Estado actual (17 de octubre de 2026)

- El modelo USD está revisado y es correcto. Faltan masas reales: hay que pesar el robot.
- Hay una IMU LSM6DS3 comprada, que llega el lunes 19 de octubre. El nuevo entrenamiento usará esa IMU.
- El entrenamiento se va a rehacer desde cero en `entrenamiento/`, paso a paso.
- El firmware con la política existe pero nunca se ha compilado ni probado en el robot.
