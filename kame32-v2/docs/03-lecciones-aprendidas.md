# Lecciones aprendidas

Lo que salió mal o costó en los intentos anteriores, para tenerlo en cuenta al rehacer el entrenamiento. El detalle completo de las recompensas está en `archivo/intento2-manager-skrl/codigo/docs/03-recompensas.md`.

## Sobre el planteamiento

- **No inventar las recompensas desde cero.** El primer intento usaba recompensas propias y nunca pasó de "funciona ligeramente, una pata se queda para arriba". El segundo copió la estructura de la tarea de locomoción oficial de Isaac Lab y las recompensas de Spot, y funcionó. Partir de algo probado y ajustar es mucho más rápido.
- **Decidir desde el principio qué sensores tendrá el robot real.** En el intento anterior se entrenó primero con datos que el robot no puede medir y se fueron quitando después, lo que obligó a reentrenar varias veces. Para el robot real son válidos: IMU (velocidad de giro y orientación), el comando de velocidad y las últimas órdenes enviadas a los servos. No lo son: la velocidad lineal del cuerpo y el ángulo real de los servos.
- **Los sensores de contacto solo para recompensas.** Sirven para premiar los pasos y detectar caídas en simulación, pero la política no debe verlos, porque el robot real no los tiene.
- **Sin ángulo de los servos, el historial importa.** Como la política no sabe dónde están las patas, necesita ver sus últimas órdenes durante varios pasos para deducirlo. Con un historial de 5 pasos funcionó.

## Sobre las recompensas

- **El robot cepillo.** Con solo premiar la velocidad, el robot aprendió a vibrar los servos menos de un grado para deslizarse sin caminar. Lo arreglaron las recompensas de Spot: premiar el tiempo de los pies en el aire y levantarlos, y castigar el deslizamiento de los pies y los cambios bruscos de acción.
- **Cuerpo bajo, pasos cortos y una pata muerta.** Se arreglaron con un premio por altura del cuerpo, más altura de pie premiada y más peso al patrón de pasos coordinado.
- **Los servos de giro apenas se movían.** El robot avanzaba solo con la elevación y parecía cojear. Se arregló premiando explícitamente la amplitud del balanceo y aflojando las penalizaciones que la frenaban sin querer, como la de alejarse de la postura de reposo.
- **Regla general:** si el movimiento es pequeño, subir un premio o bajar una penalización; si es sucio o tembloroso, subir la penalización de suavidad o de deslizamiento.

## Sobre el entorno técnico

- **Isaac Lab:** antes de ejecutar `isaaclab.sh` hay que hacer `unset VIRTUAL_ENV CONDA_PREFIX`, o no encuentra Python.
- **Número de entornos:** unos 512 entornos en paralelo van bien en este ordenador; más lo saturan.
- **El USD no estaba en git.** El `.gitignore` del repo excluye todos los USD, así que el modelo del robot solo existía en disco. En esta carpeta se ha hecho una excepción para `modelo/usd/kame32.usd`.

## Sobre el paso al robot real

- La salida de la red no se recorta: el ángulo objetivo es la postura de reposo más 0,5 por la salida. La normalización de las observaciones de skrl suma el épsilon a la raíz y recorta a ±5. Hay que replicar ambas cosas exactamente en el firmware.
- El sentido de giro de cada servo en el robot real (`SERVO_DIR` en el firmware) hay que calibrarlo a mano.
- La simulación modela servos MG90s, que son los que lleva el robot.
