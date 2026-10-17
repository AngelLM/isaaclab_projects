# Historia del proyecto

Este documento reconstruye qué se hizo y en qué orden, a partir de las fechas de los archivos, los mensajes de git y la documentación que se fue escribiendo.

## 1. El diseño original (noviembre de 2025)

Se descargó el diseño abierto de Kame32 (licencia CC BY-SA 4.0). Trae las piezas en FreeCAD, con variantes de bracket para servos SG90 y MG90s, la placa en KiCad y un firmware de PlatformIO que hace caminar al robot con osciladores, es decir, con una marcha programada a mano. Se maneja con un joystick web por WiFi. Está en `hardware/kame32-JavierIH/`.

## 2. Del CAD a la simulación (marzo de 2026)

Las piezas de FreeCAD se pasaron a Blender (`modelo/blender/kame32.blend`) para exportar STL bien posicionados y escalados (`modelo/stl/`). Con esas piezas se montó en Isaac Sim el USD del robot, con sus juntas, masas y colisiones. Hubo unas quince versiones entre el 23 y el 29 de marzo (`archivo/usd-iteraciones/kame-usd/`) hasta llegar a `kamerotated.usd`, que es el modelo definitivo (`modelo/usd/kame32.usd`).

## 3. Primer intento de entrenamiento (23 de marzo – 4 de abril de 2026)

En `~/kame` se hizo un entorno de Isaac Lab de tipo *Direct*, escrito a mano, entrenado con RSL-RL. La política veía todo lo que la simulación sabe (velocidades del cuerpo, orientación, ángulos y velocidades de los servos) y se premiaba avanzar con unas recompensas inventadas, entre ellas tener tres patas apoyadas. Los commits cuentan la evolución: "Entrenamiento mínimo", "Cambios que no funcionan", "funciona ligeramente. Una pata se queda para arriba" y, por último, "creadas configuraciones por fases", un intento de entrenar por etapas que quedó a medias y sin commitear. Se hicieron 88 entrenamientos (`~/logs/rsl_rl/kame_direct/`). Está en `archivo/intento1-direct-rslrl/`.

## 4. Segundo intento (20 de mayo – 8 de junio de 2026)

Se empezó de nuevo en `isaaclab_projects/kame32`, esta vez copiando la estructura de la tarea de locomoción oficial de Isaac Lab (tipo *manager-based*, como ANYmal o A1) y entrenando con skrl. Al principio el robot hacía trampa vibrando los servos para deslizarse ("el robot cepillo"). Se arregló copiando el conjunto de recompensas del robot Spot y, después de varios ajustes, apareció una marcha de verdad. Los sensores de contacto de los pies y del cuerpo se usaron solo para calcular recompensas y detectar caídas, nunca como entrada de la política.

Luego se fue quitando a la política lo que el robot real no puede medir, en tres variantes:

| Variante | Qué observa la política | Checkpoint |
|---|---|---|
| Privilegiada | velocidad lineal y angular del cuerpo, orientación, ángulo y velocidad de los servos, comando, última acción | `archivo/intento2-manager-skrl/checkpoints/1-privilegiado.pt` |
| Con IMU (rama `kame32-no-privilegiado`) | velocidad angular + orientación (lo que da una IMU), comando, últimas acciones, con historial de 5 pasos | `2-con-imu.pt` |
| Sin IMU (rama `kame32-noimu`) | solo el comando y las últimas acciones, con historial de 5 pasos | `3-sin-imu.pt` |

La velocidad lineal se quitó porque no se puede medir en el robot. Los ángulos de los servos se quitaron porque los MG90s no devuelven su posición. Y la IMU se quitó porque el robot real no la tiene.

## 5. Paso al robot real (8 de julio de 2026)

Se escribió un script que convierte la política sin IMU en un archivo de C (`archivo/intento2-manager-skrl/codigo/export/`) y un firmware nuevo, copia del original, que ejecuta la red a 50 Hz en lugar de los osciladores (`firmware/`). Se comprobó que la red en C da los mismos resultados que en Python, pero el firmware nunca llegó a compilarse ni a probarse en el robot.

## 6. Reorganización (octubre de 2026)

Se reunió todo en esta carpeta, se revisó el USD y se decidió rehacer el entrenamiento desde cero para entenderlo de principio a fin. También se compró una IMU LSM6DS3, de modo que el nuevo entrenamiento puede usar la orientación y la velocidad de giro del cuerpo.
