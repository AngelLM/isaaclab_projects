# Control del robot kame32 con la política de refuerzo

Esta carpeta documenta, paso a paso, cómo se ha llevado la política de caminar que entrenamos por refuerzo al robot kame32 físico, manteniendo la web y el joystick del firmware original. Está pensada para que la entiendas tú, así que va en castellano y sin dar nada por sabido.

## Qué es este proyecto

Este firmware parte del firmware original del robot, de JavierIH, y sustituye el motor de marcha. La carpeta solo contiene lo propio: la red neuronal (`lib/Policy`), el programa que la usa (`src/policy_gamepad.cpp`), la calibración de los servos de este robot (`src/config.h`) y la herramienta de calibración ampliada con una página para fijar la posición de cada servo (`src/calibration.cpp`). Las librerías `Kame` y `Octosnake`, el `gamepad.h` y el firmware de osciladores (`gamepad.cpp`) se leen sin modificar del submódulo `../hardware/kame32-JavierIH`; si esa carpeta está vacía, hay que ejecutar `git submodule update --init`. El firmware original mueve las patas con osciladores sinusoidales, es decir, con senos y cosenos ajustados a mano. Aquí, en su lugar, una pequeña red neuronal entrenada por refuerzo decide en cada instante el ángulo de las ocho articulaciones. Todo lo demás se conserva: el punto de acceso WiFi, la página web, el joystick y los botones de animaciones.

La idea es que muevas el joystick igual que antes, pero que quien coordine las patas para caminar sea la política que entrenamos en simulación, no las fórmulas de senos.

## Cómo está organizada esta documentación

El documento 01-como-funciona explica la parte conceptual, es decir, cómo se conecta la política con el robot: qué observa la red, cómo transforma esa observación en ángulos y cómo se traducen esos ángulos a los servos reales. Es el documento importante para entender el conjunto.

El documento 02-exportar-la-politica explica cómo se convierte el checkpoint del entrenamiento en un archivo que el firmware puede usar, y cómo se comprueba en el ordenador que la conversión es fiel.

El documento 03-compilar-y-flashear explica cómo compilar y subir el firmware al ESP32 con PlatformIO, y cómo leer la autoverificación que hace el robot al arrancar.

El documento 04-calibracion-y-puesta-en-marcha es el más práctico. Explica cómo poner el robot en marcha con seguridad, cómo comprobar que cada servo se mueve en el sentido correcto y cómo ajustarlo si no es así, y cómo se interpreta el joystick.

El documento 05-limitaciones es una explicación honesta de qué esperar y qué no. Es importante leerlo, porque llevar una política de la simulación a un robot real casi nunca sale perfecto a la primera.

## Resumen muy rápido del flujo de trabajo

Primero se entrena la política en simulación (eso ya está hecho, en el proyecto de Isaac Lab). Después, en el ordenador, se corre un script que lee el checkpoint y genera un archivo de cabecera en C con los pesos de la red. Ese archivo se incrusta en este firmware. Por último se compila y se sube el firmware al robot, se comprueba que arranca bien, se calibra el sentido de los servos y se prueba con el joystick.
