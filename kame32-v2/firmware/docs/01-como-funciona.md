# Cómo funciona el control por política

Este documento explica cómo encaja la red neuronal entrenada con el robot real. Conviene entenderlo antes de tocar nada, porque los detalles importan y un error pequeño aquí hace que el robot no camine.

## La idea general

La política es una red neuronal pequeña. En cada instante recibe una entrada (lo que llamamos la observación), hace unos cuantos cálculos y produce ocho números, uno por servo. Esos ocho números no son ángulos directos, sino desviaciones respecto a la postura de reposo del robot. La red se ejecuta cincuenta veces por segundo, que es exactamente el ritmo al que se entrenó en simulación.

Lo bonito de este robot es que la postura de reposo de la simulación coincide con la postura home del firmware original, es decir, la postura de pie neutra. Como la red trabaja siempre en desviaciones respecto a esa postura, trasladar su salida al robot real se reduce en gran parte a colocar bien la postura de reposo y a acertar el sentido de giro de cada servo.

## Qué observa la red

En la variante que hemos desplegado, el robot no tiene ningún sensor. Esto se decidió a propósito porque puede que no se le monte una unidad inercial. La red por tanto no siente el suelo ni su inclinación. Lo único que conoce es el comando de velocidad que le llega del joystick y el recuerdo de sus propias acciones recientes.

En concreto, la observación tiene cincuenta y cinco números. Se forma así. Por un lado está el comando de velocidad, que son tres números: la velocidad hacia delante, la velocidad lateral (que siempre vale cero, porque el robot no aprendió a desplazarse de lado) y la velocidad de giro. Por otro lado está la última acción que la red produjo, que son ocho números. Como una sola foto instantánea da muy poca información cuando no hay sensores, se apilan las cinco fotos más recientes. Así la red ve una pequeña película de lo que ha pasado en los últimos cien milisegundos, y de ahí deduce en qué punto del ciclo de la marcha se encuentra.

El orden exacto de esos cincuenta y cinco números es importante y hay que respetarlo al construir la observación en el firmware. Primero van los cinco comandos, del más antiguo al más reciente, tres números cada uno, lo que da quince números. Después van las cinco acciones, también del más antiguo al más reciente, ocho números cada una, lo que da cuarenta números. Quince más cuarenta son cincuenta y cinco. El firmware lo construye exactamente en ese orden.

## El pequeño desfase temporal

Hay un detalle sutil que se ha reproducido con cuidado. En la simulación, la observación con la que la red decide la acción de un instante contiene, como acción más reciente, la del instante anterior. Es decir, la red siempre mira su acción previa para decidir la siguiente. El firmware hace lo mismo: en cada paso apila en la memoria la pareja formada por el comando actual y la acción del paso anterior, y con eso construye la observación para calcular la acción de ahora. Respetar esto es lo que hace que el comportamiento en el robot se parezca al de la simulación.

## Cómo calcula la red

La red es un perceptrón multicapa. La observación de cincuenta y cinco números pasa primero por una normalización, que resta una media y multiplica por una escala fijas, aprendidas durante el entrenamiento, y recorta el resultado a un rango de más menos cinco. Esa normalización es idéntica a la que se usó al entrenar, porque si no la red recibiría números en una escala distinta a la que espera y se comportaría de forma extraña. Después vienen tres capas ocultas de ciento veintiocho neuronas cada una, con una función de activación llamada ELU, y una capa final que produce los ocho números de salida. No hay ninguna otra transformación, ni recortes ni funciones raras al final.

Todo esto en el ESP32 son unas setenta mil multiplicaciones por paso, que para el procesador del robot es un esfuerzo insignificante. Se ejecuta a mano en C, sin librerías pesadas, porque para una red tan pequeña no hace falta nada más.

## De la salida de la red al ángulo del servo

Cada uno de los ocho números de salida corresponde a una articulación de la simulación. Para convertirlo en un ángulo de servo se hacen dos pasos. Primero, la salida se multiplica por un factor de un medio y se interpreta como una desviación en radianes respecto a la postura de reposo, tal y como se hacía en el entrenamiento. Segundo, esa desviación se pasa a grados y se suma al ángulo de reposo del servo correspondiente, que es el mismo de la postura home del firmware.

Hay que tener en cuenta dos correspondencias. Una es que el orden de las articulaciones en la simulación no es el mismo que el orden de los servos en la placa, así que hay una tabla que dice qué articulación de la simulación va a qué servo físico. La otra es que el sentido de giro de un servo en el robot puede estar montado al revés que en la simulación, así que hay un número por servo, más uno o menos uno, que indica su sentido. Ese número es lo único que probablemente haya que ajustar a mano probando con el robot, y de eso trata el documento de calibración.

## Qué pasa con el joystick y los botones

El joystick se lee igual que en el firmware original, con valores de menos cien a cien en cada eje. El eje de adelante y atrás se convierte en la velocidad hacia delante, y el eje de izquierda y derecha se convierte en la velocidad de giro. A diferencia del firmware original, que elegía entre avanzar o girar, aquí se pasan las dos cosas a la vez, porque la política sabe combinar avance y giro. Cuando el joystick está en el centro, el comando es cero y la política se queda quieta en su postura.

Los botones de animaciones se han dejado tal cual. Siguen llamando a las rutinas que ya traía el robot, como saludar o bailar. Son acciones puntuales que interrumpen un momento la marcha y luego esta continúa.
