# Uso y ajuste

Este documento es la parte práctica: cómo poner en marcha el entrenamiento, cómo ver el resultado, cómo medir si el robot se mueve como queremos y qué tocar cuando algo no sale bien.

## Un detalle imprescindible antes de cualquier comando

En esta máquina la variable de entorno VIRTUAL_ENV está puesta a "/usr", y eso despista al lanzador de Isaac Lab, que se pone a buscar un Python que no existe y falla nada más empezar. La solución es desactivar esa variable (y por si acaso también CONDA_PREFIX) antes de lanzar nada. Todos los comandos de aquí abajo dan por hecho que primero se ha ejecutado esto:

```
unset VIRTUAL_ENV CONDA_PREFIX
```

El intérprete de Python que tiene Isaac Lab se usa a través del lanzador, que en esta máquina está en "/home/angellm/IsaacLab/isaaclab.sh". Se usa con la opción "-p" seguida del script.

## Instalar el proyecto

El proyecto es un paquete de Python instalable en modo editable. Hay que instalarlo una vez, y volver a instalarlo solo si se cambian los archivos de empaquetado. Desde la carpeta del proyecto:

```
/home/angellm/IsaacLab/_isaac_sim/python.sh -m pip install -e source/kame32
```

## Entrenar

El entrenamiento se lanza con el script de skrl, sin ventana (con la opción headless) y con varias copias del robot en paralelo. Para este robot va bien usar del orden de 512 copias, que es un buen equilibrio entre velocidad y carga de la máquina:

```
/home/angellm/IsaacLab/isaaclab.sh -p scripts/skrl/train.py --task Template-Kame32-v0 --headless --num_envs 512 --max_iterations 1500
```

El número de iteraciones se puede subir o bajar. Conviene recordar que cada iteración son varios pasos de simulación (en concreto, el número de iteraciones multiplicado por los pasos de rollout da el total de pasos de entrenamiento). Con 1500 iteraciones salen unos 36000 pasos. Con más entrenamiento la marcha sale más pulida. Los resultados se guardan en una subcarpeta con la fecha dentro de "logs/skrl/kame32_walk", incluidos los puntos de control para reproducir luego y los registros para TensorBoard.

## Ver una política entrenada

Para ver al robot moverse con una política ya entrenada se usa el script de reproducción, que carga el último punto de control o uno que se le indique. Aquí conviene usar la variante de visualización de la tarea, que pone pocos robots y desactiva la aleatorización para que se vea limpio:

```
/home/angellm/IsaacLab/isaaclab.sh -p scripts/skrl/play.py --task Template-Kame32-Play-v0 --num_envs 16
```

La variante de visualización ordena una velocidad fija hacia delante para que se vea una marcha clara, y muestra encima del robot dos flechas, una hacia delante para la velocidad lineal y otra hacia el lado para el giro (apunta al lado al que gira y desaparece cuando va recto), en verde lo que se ordena y en azul lo que el robot hace. Si se quiere ver el robot a otra velocidad o girando, se puede editar esa velocidad en la variante de visualización dentro del archivo de configuración del entorno.

Para grabar un vídeo en lugar de mirarlo en directo se añade la opción de vídeo al comando de reproducción.

## Medir cuánto se mueve cada articulación

Como el objetivo es que los movimientos sean amplios, hay un script propio que mide el recorrido real de cada articulación con una política entrenada. Carga un punto de control, deja correr la política un rato y al final imprime, para cada articulación, el ángulo mínimo, el máximo, el recorrido total y la desviación, todo en grados:

```
/home/angellm/IsaacLab/isaaclab.sh -p scripts/inspect_motion.py --task Template-Kame32-Play-v0 --num_envs 64 --steps 400
```

Esta es la forma más directa de comprobar si los servos están haciendo recorridos amplios o si se han quedado en movimientos diminutos. Si se quiere mirar un punto de control concreto, se le pasa con la opción de checkpoint.

Hay además una segunda forma de ver lo mismo, que no hace falta lanzar a mano, porque se calcula durante el propio entrenamiento. En TensorBoard, dentro del grupo "Info", aparece una variable por cada servo llamada "JointRange" seguida del nombre de la articulación, que indica el rango en grados que ese servo ha recorrido de media por episodio. Mirando esas curvas mientras entrena se ve enseguida si los servos de elevación están ganando recorrido o si se están quedando quietos, sin necesidad de reproducir nada. Para abrir TensorBoard se apunta a la carpeta "logs/skrl/kame32_walk".

## Las perillas de ajuste más útiles

Cuando algo no sale bien, casi siempre se arregla tocando uno de estos sitios.

Si la marcha sale temblorosa o con micromovimientos, conviene subir la penalización por cambios bruscos de acción y revisar la penalización por deslizamiento del pie. Si por el contrario los movimientos son demasiado pequeños y parece que cojea, conviene subir los premios al balanceo de las articulaciones, subir el premio al despeje del pie y bajar las penalizaciones que frenan la amplitud, como la de desviarse de la postura de reposo y la de velocidad de las articulaciones.

Si el cuerpo va demasiado pegado al suelo, se sube el premio a la altura del cuerpo o se cambia la postura de reposo a una más alta. Si en cambio el cuerpo va demasiado tieso y no oscila nada, se baja ese premio o la penalización al movimiento del cuerpo.

Si una pata se queda muerta, se sube la penalización por desigualdad en los tiempos de las patas y el premio al patrón de marcha.

Si se quiere cambiar el rango de velocidades o de giros, se editan los rangos del comando en la configuración del entorno. Y si el robot no llega a las velocidades altas que se le piden, lo más probable es que se esté quedando corto el límite de velocidad del servo, que se sube en la configuración del robot, teniendo en cuenta que eso se aleja del servo barato real.

La rigidez y la amortiguación de los servos también son perillas importantes. Más rigidez hace el movimiento más decidido pero puede volverlo nervioso, y más amortiguación lo suaviza pero puede volverlo lento.

## Notas para pasar al robot real

El robot real lleva una placa ESP32, servos pequeños y una unidad inercial. La política ya está entrenada usando solo lo que ese robot puede medir, así que no usa datos privilegiados. Lo que observa es la inclinación y la velocidad de giro del cuerpo (de la unidad inercial), el comando de velocidad y el último comando de posición que envió a los servos, más un historial corto de todo eso. En concreto, no usa la velocidad lineal del cuerpo (que no se puede medir fácilmente) ni la posición real de los servos (que estos servos no devuelven), y de la posición de las patas se fía del último comando que les mandó. El sensor de contacto de los pies tampoco es un problema, porque solo se usa para calcular recompensas durante el entrenamiento y no forma parte de lo que la política observa. En resumen, el paso al robot real es directo en cuanto a sensores, y lo que quedaría por resolver es el ajuste fino del modelo de servo y la calibración de la unidad inercial.

Hay que tener en cuenta también que el modelo de servo que se usa ahora es de tipo MG90s, más rápido que el SG90. Si el robot real monta SG90, conviene bajar en la configuración el límite de velocidad del servo a un valor realista y volver a entrenar, para que la marcha aprendida no dependa de una velocidad que el servo real no puede dar.
