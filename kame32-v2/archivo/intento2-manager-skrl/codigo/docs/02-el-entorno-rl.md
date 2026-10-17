# El entorno de aprendizaje

Este documento describe cómo está montado el entorno de refuerzo, es decir, todo lo que rodea al robot durante el entrenamiento: qué percibe, qué puede hacer, qué se le pide, cómo se le añade variedad y con qué parámetros corre la simulación. El entorno está construido con el flujo de trabajo de tareas basadas en managers de Isaac Lab, copiando la estructura de la tarea de locomoción por velocidad que trae Isaac Lab para robots con patas, pero adaptada al tamaño y a la mecánica de kame32.

## La tarea

La tarea es de seguimiento de velocidad. En cada momento el robot recibe una orden que dice cuánto debe avanzar hacia delante y cuánto debe girar, y su trabajo es moverse de forma que su velocidad real se parezca a esa orden. Caminar hacia delante a distintas velocidades y girar a un lado o a otro son simplemente casos particulares de esta misma tarea. Esta forma de plantearlo es la estándar en locomoción con patas porque es flexible: una vez que el robot sabe seguir órdenes de velocidad, se le puede pedir cualquier trayectoria.

## Las observaciones

Esta variante del entrenamiento es a ciegas, es decir, sin ningún sensor. Se ha preparado para el caso de que no se pueda montar una unidad inercial en el robot. La política no recibe ninguna realimentación del mundo: en cada paso solo ve el comando de velocidad actual (tres números) y el último comando de posición que ella misma envió a los servos (ocho números). En total, once números por paso.

El motivo es la limitación del robot real. Los servos son de aficionado y no devuelven su posición, así que la política no puede saber en qué ángulo está cada pata, y lo único que conoce de ellas es el último comando que les mandó, del que deduce aproximadamente dónde están. La velocidad lineal del cuerpo no se mide. Y si además se quita la unidad inercial, desaparece también la inclinación y la velocidad de giro, que eran lo único que le daba sentido del equilibrio. Lo que queda es una política que aprende un patrón de marcha cíclico y lo reproduce, como quien repite unos pasos de memoria, sin sentir el suelo ni notar si se está cayendo. Por eso se dice que es feedforward o a ciegas, y deja de ser reactiva: no puede percibir un tropiezo o un empujón y corregirlo.

Justo porque no hay sensores, el historial de acciones pasa a ser todavía más importante, ya que es la única pista temporal que tiene la política para saber en qué punto del ciclo de marcha se encuentra. Se apilan las últimas cinco observaciones, de modo que la red ve la secuencia reciente de comandos y de comandos enviados a los servos. Esto no es hardware extra, solo memoria de la propia política. Con eso, la observación final que entra en la red es de once por cinco, es decir, cincuenta y cinco números.

Conviene tener presente que entrenar a ciegas es bastante más difícil que con una unidad inercial, y que una marcha aprendida así suele ser menos estable y peor para girar, porque el robot no puede reaccionar a lo que no siente. Es una solución de compromiso pensada para cuando no hay más remedio. Existe también una variante con unidad inercial, que añade la velocidad de giro y la dirección de la gravedad a la observación, y que es la recomendable siempre que se pueda montar ese sensor.

## Las acciones

La política produce ocho números, uno por servo. Cada número es un ángulo objetivo, pero no absoluto, sino sumado a la postura de reposo. Es decir, una acción de cero significa quedarse en la postura de reposo, y valores positivos o negativos mueven cada servo a un lado u otro de esa postura. Los ángulos objetivo se escalan por un factor de 0.5, que da un margen de movimiento amplio, de más de veinte grados, suficiente para zancadas grandes. El control de posición de cada servo se encarga de llevar la articulación al ángulo pedido.

## Los comandos de velocidad

El comando se genera de forma aleatoria y se vuelve a sortear cada pocos segundos, en concreto entre cada tres y cinco segundos, para que dentro de un mismo episodio el robot vea varias órdenes distintas. La velocidad hacia delante se sortea entre menos 0.15 y 0.45 metros por segundo, lo que incluye marcha atrás suave, marcha muy lenta y marcha rápida, dando mucha variedad. El giro se sortea entre menos uno y uno radianes por segundo, lo que obliga al robot a aprender a girar de verdad. No se ordena desplazamiento lateral, porque para esta marcha interesa centrarse en avanzar y girar. Una pequeña fracción de los entornos recibe la orden de quedarse quietos, para que también aprenda a mantenerse en pie sin moverse.

El comando se dibuja en pantalla con flechas, justo encima del robot. Hay una visualización para la velocidad lineal y otra para la velocidad angular, hechas con una clase de comando propia (Kame32VelocityCommand) porque la de Isaac Lab solo dibuja la lineal y además la coloca muy alta, pensada para robots grandes. La velocidad lineal se ve como una flecha horizontal que apunta en la dirección de avance y cuya longitud crece con la velocidad. La velocidad angular se ve como otra flecha horizontal, pero perpendicular, que apunta hacia el lado al que gira el robot, a su izquierda cuando gira a la izquierda y a su derecha cuando gira a la derecha, con una longitud que crece con el ritmo de giro y que desaparece cuando el robot va recto. Las dos flechas salen del mismo punto, así que juntas forman una ele y se distinguen bien (la de avance hacia delante, la de giro hacia el lado). En ambos casos el verde marca lo que se ordena y el azul lo que el robot hace de verdad, así que de un vistazo se ve si el robot está siguiendo bien la orden. El tamaño de las flechas está ajustado a la escala de kame32 para que se vean bien sin tapar al robot.

## La aleatorización

Para que la política no se acostumbre a un único conjunto de condiciones, el entorno introduce variedad de varias formas. Al inicio de cada entorno se sortea la fricción del suelo dentro de un rango, y se le suma o resta un poco de masa al chasis. En cada reinicio se coloca el robot con una posición y una orientación algo distintas y con una pequeña velocidad inicial, y se desvían un poco los ángulos de los servos respecto a la postura de reposo. Y cada cierto tiempo, durante el episodio, se le da un empujón aleatorio al cuerpo para comprobar que es capaz de recuperar el equilibrio. Todo esto hace que la marcha aprendida sea más estable y menos frágil.

## La simulación

La física se calcula a 200 pasos por segundo, y la política toma una decisión una de cada cuatro veces, lo que da una frecuencia de control de 50 decisiones por segundo. Cada episodio dura como mucho quince segundos, salvo que el robot se caiga antes. El suelo es un plano con fricción. Se entrenan varias copias del robot a la vez, lo que hace que el aprendizaje avance rápido a pesar de la complejidad del problema (en la práctica se ha usado del orden de 512 copias, que es un buen equilibrio para este robot).

El episodio también puede terminar antes de tiempo por dos motivos de fracaso: que el chasis toque el suelo, lo que se detecta con un sensor de contacto, o que el robot se incline demasiado, más de unos cuarenta y seis grados respecto a la vertical. Cuando ocurre uno de estos fracasos, el episodio se corta, lo que reduce la recompensa total que el robot puede acumular y por tanto lo empuja a no caerse.

## El sensor de contacto

Hay un sensor de contacto montado en todos los cuerpos del robot. Es importante señalar que ese sensor no entra en las observaciones de la política, solo se usa para calcular algunas recompensas y la condición de caída. Es decir, el robot no percibe el contacto para decidir, solo lo usamos nosotros para premiarlo o penalizarlo. Esto encaja con la idea de mantener al mínimo los sensores que harían falta en el robot real.

## El algoritmo y la red

El algoritmo de aprendizaje es PPO, ejecutado a través de la librería skrl. La red neuronal es un perceptrón multicapa con tres capas ocultas de 128 neuronas cada una y activación elu, que es de sobra para un robot de ocho servos. Las observaciones y los valores se normalizan automáticamente durante el entrenamiento, lo que ayuda mucho cuando hay magnitudes de escalas muy distintas mezcladas en la observación. Los registros de cada entrenamiento, incluidos los puntos de control para reproducir luego, se guardan en la carpeta "logs/skrl/kame32_walk".

Además de las recompensas, el entorno registra en TensorBoard una variable por cada uno de los ocho servos con el rango en grados que ha recorrido durante el episodio. Esto se consigue con una subclase del entorno (Kame32Env) que lleva la cuenta del ángulo mínimo y máximo de cada servo y, al terminar cada episodio, apunta la diferencia. Esas variables aparecen en TensorBoard como "Info / JointRange/" seguido del nombre de la articulación, y sirven para ver de un vistazo cuánto se mueve cada servo, en particular para comprobar si los de elevación se están moviendo lo suficiente o se están quedando demasiado quietos.
