# Exportar la política al firmware del robot

Aquí se convierte la política entrenada (la variante sin IMU) en un archivo de cabecera en C que se incrusta en el firmware del ESP32. Todo el detalle está en la documentación del proyecto del robot, en la carpeta docs de kame32-rl. Esto es solo la referencia rápida.

## El checkpoint

En esta carpeta hay un archivo checkpoint.pt. Es el checkpoint que se va a exportar. Ahora mismo contiene la política sin IMU que entrenamos, pero puedes sustituirlo por el que prefieras: copia encima el archivo best_agent.pt (o el agent_XXXX.pt que quieras) del run que elijas, que están en logs/skrl/kame32_walk. Tiene que ser un run entrenado con la observación sin IMU (de 55), porque el firmware espera exactamente esa forma.

## Correr la exportación

Desde la carpeta del proyecto de entrenamiento (kame32), con el entorno de Isaac Lab:

```
unset VIRTUAL_ENV CONDA_PREFIX
/home/angellm/IsaacLab/isaaclab.sh -p export/export_policy.py
```

Esto hace tres cosas. Primero comprueba que su propia forma de calcular la política (la que se porta a C) coincide con la de skrl, y lo dice con un número de error que debe ser diminuto (del orden de 1e-7). Segundo, escribe el archivo policy_weights.h dentro del firmware, en kame32-rl/lib/Policy. Tercero, deja preparado dentro de ese archivo un caso de prueba (una observación de ejemplo y la salida que debe dar) para que el propio ESP32 pueda verificar al arrancar que su inferencia es correcta.

Si quieres además un archivo ONNX para inspeccionarlo en el ordenador, añade la opción --onnx y se genera policy.onnx en esta carpeta. El ESP32 no usa el ONNX, solo el header en C.

## Qué contiene el header generado

El archivo policy_weights.h lleva las dimensiones de la red, la normalización de las observaciones ya preparada (la media y la inversa de la desviación, para que el ESP32 no tenga que hacer raíces cuadradas y para que la normalización sea idéntica a la del entrenamiento, incluido el recorte a mas menos cinco), todos los pesos y sesgos de las cuatro capas, y el caso de prueba. No hay que tocarlo a mano, se regenera cada vez que corres el script.
