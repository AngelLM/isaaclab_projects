# Compilar y subir el firmware al robot

Este documento explica cómo compilar el firmware nuevo y subirlo al ESP32, y cómo comprobar que ha arrancado bien. Se usa PlatformIO, igual que en el firmware original.

## Los tres entornos de compilación

El archivo platformio.ini de este proyecto define tres entornos. El primero es calibration, que es la herramienta original para ajustar los servos y no se ha tocado. El segundo es gamepad, que es el firmware original con los osciladores, que se ha conservado intacto por si quieres volver a él. El tercero es policy, que es el nuevo, el que usa la red neuronal. Para el control por política hay que compilar y subir el entorno policy.

## Antes de compilar

Asegúrate de haber generado el archivo policy_weights.h, tal y como se explica en el documento de exportación. Sin ese archivo el entorno policy no compila, porque es donde están los pesos de la red. Si has entrenado una política nueva, acuérdate de exportarla de nuevo antes de compilar, o el robot seguirá usando los pesos viejos.

## Compilar

Desde la carpeta firmware (con el submódulo descargado), con PlatformIO instalado, se compila el entorno policy con el comando de compilación de PlatformIO indicando ese entorno. En la interfaz de Visual Studio Code con la extensión de PlatformIO también se puede elegir el entorno policy y darle a construir. Si compila sin errores, ya está listo para subir.

Ten en cuenta que este firmware incrusta todos los pesos de la red, que ocupan algo más de medio megabyte en el programa. Es perfectamente asumible para el ESP32, que tiene de sobra, pero es normal que el archivo compilado sea más grande que el del firmware original.

## Subir al robot

Conecta el ESP32 por el cable USB y sube el firmware con el comando de subida de PlatformIO para el entorno policy, o con el botón de subir de la extensión. Es el mismo procedimiento que usabas con el firmware original.

## La autoverificación al arrancar

Cuando el robot arranca con el firmware de política, lo primero que hace, además de levantar el WiFi y colocarse en la postura de reposo, es una autoverificación de la red. Coge el caso de prueba que quedó grabado en la cabecera, lo pasa por la red que corre en el ESP32 y comprueba que el resultado coincide con el que se calculó en el ordenador. Si coincide, escribe por el puerto serie un mensaje diciendo que la autoverificación es correcta. Si no coincide, avisa de que ha fallado.

Para ver ese mensaje, abre el monitor del puerto serie de PlatformIO a ciento quince mil doscientos baudios justo después de subir el firmware o al reiniciar el robot. Si ves el mensaje de que la autoverificación es correcta, tienes la garantía de que la red está bien copiada y bien ejecutada en el robot, y que cualquier problema de marcha que aparezca después no es de la red sino de la parte física, es decir, del sentido de los servos o de la mecánica. Esta separación es muy útil para no volverte loco buscando el problema donde no está.

## Conectarse al robot

El robot crea su propio punto de acceso WiFi, con el nombre y la contraseña que están en el archivo de configuración, igual que antes. Conéctate a esa red desde el móvil o el ordenador y abre la página del robot en el navegador, en la dirección que ya usabas. Verás el mismo joystick y los mismos botones de siempre. La diferencia está por dentro: ahora quien mueve las patas es la política.
