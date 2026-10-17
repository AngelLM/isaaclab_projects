# Exportar la política al firmware

Este documento explica cómo se convierte la política entrenada en un archivo que el firmware del robot puede usar. Este paso se hace en el ordenador, en el proyecto de entrenamiento de Isaac Lab, no en el robot.

## Por qué hace falta este paso

La política entrenada vive en un checkpoint, que es un archivo de PyTorch con los pesos de la red y algunos datos más. El ESP32 no puede leer directamente un checkpoint de PyTorch, ni tiene sentido meterle PyTorch ni un motor de ONNX, porque son demasiado pesados para un microcontrolador. Lo que se hace es mucho más sencillo y robusto: un script lee el checkpoint en el ordenador y escribe un archivo de cabecera en C con todos los números de la red. Ese archivo se incrusta en el firmware y la red se ejecuta a mano, que para una red tan pequeña es trivial.

## Dónde está el script y el checkpoint

En el proyecto de entrenamiento, dentro de la carpeta kame32, hay una carpeta llamada export. Dentro están el script export_policy.py y un archivo checkpoint.pt. Ese checkpoint.pt es el que se va a exportar. Ya contiene la política sin unidad inercial que entrenamos, pero puedes sustituirlo por otro si quieres: basta con copiar encima el archivo del run que prefieras, que se llama best_agent.pt o agent seguido de un número, y está en la carpeta de logs del entrenamiento. Lo único imprescindible es que sea un run entrenado con la observación sin sensor, la de cincuenta y cinco números, porque el firmware espera exactamente esa forma.

## Cómo se corre

Desde la carpeta kame32 del proyecto de entrenamiento, usando el intérprete de Isaac Lab, se ejecuta el script. En esta máquina, como la variable de entorno de los entornos virtuales despista al lanzador, primero hay que desactivarla. Los dos comandos son estos.

```
unset VIRTUAL_ENV CONDA_PREFIX
/home/angellm/IsaacLab/isaaclab.sh -p export/export_policy.py
```

El script hace tres cosas. La primera es una comprobación de seguridad: calcula la salida de la red de dos maneras distintas, una con su propio código, que es el que se copia al robot, y otra usando las herramientas originales de la librería de entrenamiento, y compara. Si el error entre ambas es diminuto, del orden de una diezmillonésima, es que la conversión es fiel y lo dice por pantalla. La segunda cosa es escribir el archivo de cabecera policy_weights.h dentro del firmware, en la carpeta lib de la librería Policy. La tercera es dejar preparado dentro de ese archivo un caso de prueba, es decir, una observación de ejemplo junto con la salida que la red debe dar, para que después el propio robot pueda verificarse al arrancar.

Si además quieres un archivo en formato ONNX para inspeccionar la red en el ordenador con otras herramientas, puedes añadir al comando la opción de ONNX y se genera un archivo aparte. El robot no usa ese archivo, solo la cabecera en C, pero puede venir bien para mirar la red.

## Qué se ha comprobado ya

Al preparar todo esto se verificó que la implementación en C de la red produce exactamente la misma salida que la política original de PyTorch, con una diferencia de una diezmillonésima, que es simplemente el redondeo normal de los números decimales. Es decir, la parte de que la red esté bien copiada al robot está resuelta y comprobada. Lo que queda por ajustar en el robot no es la red, sino la parte física de los servos, que se trata en el documento de calibración.

## Cuándo hay que repetir este paso

Cada vez que entrenes una política nueva y quieras probarla en el robot, tienes que repetir la exportación: copiar el nuevo checkpoint sobre checkpoint.pt, correr el script otra vez para regenerar la cabecera, y volver a compilar y subir el firmware. La cabecera no se edita nunca a mano.
