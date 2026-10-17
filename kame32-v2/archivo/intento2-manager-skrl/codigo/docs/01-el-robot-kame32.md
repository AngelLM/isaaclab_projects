# El robot kame32

## Qué es

kame32 es un robot cuadrúpedo de tipo araña. No es un robot tipo perro con patas debajo del cuerpo, sino una araña con las patas saliendo hacia los lados. Es un rediseño del conocido MiniKame, pensado para usar piezas baratas y fáciles de conseguir. Mide alrededor de 15 centímetros y pesa unos 330 gramos. El control real lo lleva una placa ESP32 y los movimientos los hacen servos pequeños de aficionado, del tipo SG90 o MG90s.

## Las patas y sus grados de libertad

Cada una de las cuatro patas tiene dos grados de libertad, es decir, dos servos. El primero gira toda la pata alrededor de un eje vertical, lo que permite moverla hacia delante y hacia atrás como si remara. A este movimiento lo llamamos giro o, en inglés, yaw. El segundo servo sube y baja la pata. Aquí está la gracia mecánica del robot: en lugar de doblar la pata como una rodilla, usa un paralelogramo (un mecanismo de cuatro barras) que sube y baja el extremo de la pata manteniéndolo siempre perpendicular al suelo. Gracias a eso el pie no cambia de inclinación al subir o bajar, lo que simplifica mucho la marcha.

En resumen, hay ocho servos de verdad: cuatro de giro y cuatro de elevación. Esos son los únicos motores que el robot real puede mover, y por tanto son las únicas articulaciones que la política de control va a comandar.

## Cómo se ve todo esto dentro del simulador

Cuando se carga el archivo USD del robot en Isaac Lab y se inspecciona la articulación, aparecen dieciséis grados de libertad, no ocho. Esto sorprende al principio, pero tiene una explicación clara. El motor de física trabaja con árboles de cuerpos rígidos unidos por articulaciones, y el paralelogramo de cada pata, al ser un lazo cerrado, se modela con varias articulaciones extra.

De esos dieciséis grados de libertad, ocho son los servos reales y los otros ocho son las articulaciones pasivas del paralelogramo. Las pasivas no llevan motor, se mueven solas arrastradas por la mecánica. Para que el lazo del paralelogramo quede cerrado de verdad, el USD incluye además cuatro articulaciones más que están marcadas como excluidas de la articulación principal. Esas cuatro funcionan como restricciones físicas que cierran el cuadrilátero, y son las que consiguen que el pie se mantenga perpendicular sin que nadie lo controle activamente. Esto se comprobó en simulación dejando caer el robot y viendo que el pie se mantiene horizontal y que las articulaciones pasivas se acomodan solas.

La conclusión práctica es importante: en el archivo de configuración del robot solo se le ponen ganancias de control a los ocho servos reales. A las ocho articulaciones pasivas se les dejan ganancias a cero para que queden libres, y el cierre del lazo se encarga del resto.

## Nombres de cuerpos y articulaciones

Conviene conocer los nombres porque aparecen por todas partes en la configuración del entorno.

El cuerpo central, el chasis, se llama "Body" y es el cuerpo raíz del robot. Cuelgan de él los soportes de cadera, llamados "Bracket", uno por pata. De cada soporte sale la pata, llamada "Leg", y al final está el pie, llamado "Foot". Las barras del paralelogramo se llaman "Link". Los sufijos indican la posición: LeftFront es delantera izquierda, RightFront delantera derecha, LeftBack trasera izquierda y RightBack trasera derecha.

Las cuatro articulaciones de giro se llaman Body_BLB, Body_BRB, Body_BLF y Body_BRF, y giran sobre el eje vertical. Las cuatro de elevación se llaman BLB_LLB, BRB_LRB, BLF_LLF y BRF_LRF, y giran sobre un eje horizontal. Las pasivas del paralelogramo empiezan por L y contienen una F (por ejemplo LLB_FLB o LkLB_FLB).

## Masas

El reparto de masa es muy desigual, como cabe esperar de un robot tan pequeño. El chasis pesa unos 110 gramos, cada soporte de cadera unos 25 gramos, y las patas, los pies y las barras del paralelogramo unos 10 gramos cada pieza. Sumando todo da alrededor de 330 gramos.

## La postura de reposo

Si se ponen todas las articulaciones a cero, el robot queda estable y nivelado, pero muy aplastado contra el suelo, con el cuerpo a unos 3.2 centímetros de altura. Esa postura tan baja deja poco margen para levantar y balancear las patas, así que en la configuración se parte de una postura más alta. Para subir el cuerpo hay que girar los servos de elevación en sentidos contrarios según el lado (los izquierdos en negativo y los derechos en positivo, por la simetría del montaje). Con un giro moderado el cuerpo sube a unos 5 centímetros manteniéndose nivelado, y esa es la postura de reposo que se usa por defecto. La altura inicial de aparición se pone un poco por encima, alrededor de 6 centímetros, para que el robot no nazca atravesando el suelo y se asiente en sus primeros instantes.

## El modelo de servo

Los servos se modelan como actuadores de posición, que es justo como funciona un servo de verdad: se le da un ángulo objetivo y él intenta llegar a ese ángulo. En la configuración se modela un servo rápido tipo MG90s, con un límite de velocidad de 14 radianes por segundo y un par máximo de 0.20 newton metro. Se eligió el MG90s en lugar del SG90 más lento porque queremos que el robot pueda alcanzar velocidades altas, y un SG90 (que ronda los 10 radianes por segundo) se quedaría corto. La rigidez y la amortiguación del control de posición están en 6.0 y 0.2 respectivamente, valores que sujetan bien la postura y que se pueden retocar si la marcha sale demasiado rígida o demasiado blanda.

## Un detalle técnico que costó un rato

La ruta del archivo USD tiene que pasarse como texto, no como objeto de ruta de Python. Isaac Lab hace internamente una comprobación tratando la ruta como una cadena de texto, y si se le pasa un objeto de ruta directamente, falla al cargar el robot. Por eso en la configuración la ruta se envuelve siempre en una conversión a texto.
