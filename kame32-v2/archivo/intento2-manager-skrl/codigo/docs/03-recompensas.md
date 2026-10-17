# Las recompensas

Este es el documento más importante, porque en aprendizaje por refuerzo el comportamiento que acaba aprendiendo el robot lo decide casi por completo el diseño de las recompensas. El robot no sabe lo que es "caminar bonito", solo busca maximizar la suma de recompensas. Si una forma fea de moverse da más recompensa que una bonita, el robot elegirá la fea. Por eso la mayor parte del trabajo de este proyecto ha consistido en afinar estas recompensas hasta que la única forma de ganar puntos sea moverse como queremos.

Antes de listar los términos conviene contar la historia, porque explica por qué el diseño es como es y no más simple.

## La historia de los fallos y cómo se arreglaron

### El robot cepillo

El primer diseño fue el más obvio: premiar al robot por seguir el comando de velocidad, darle un pequeño premio por seguir vivo y penalizarlo por caerse, más unas pocas penalizaciones suaves. Sobre el papel parecía suficiente. El resultado fue un fraude. El robot descubrió que podía hacer vibrar sus servos a toda velocidad con movimientos diminutos, de menos de un grado, y que esa vibración, combinada con el contacto de los pies, lo hacía deslizarse por el suelo como un cepillo vibrador. Avanzaba, sí, y la recompensa de seguimiento de velocidad llegaba a valores altísimos, pero no estaba caminando en absoluto. Como nunca levantaba los pies ni se caía, tampoco activaba ninguna penalización.

Este es un caso de manual de lo que se llama reward hacking, que es cuando el agente encuentra una grieta en las recompensas y la explota. La lección fue que premiar la velocidad no basta, porque hay maneras baratas y feas de conseguir velocidad.

### Adoptar el conjunto de recompensas de Spot

La solución fue dejar de inventar y copiar el conjunto de recompensas que Isaac Lab usa para el robot Spot, que está cuidadosamente afinado precisamente para producir marchas naturales y para evitar estos fallos. Ese conjunto no solo premia ir a la velocidad pedida, sino que premia levantar los pies y dar pasos de duración razonable, premia despegar el pie del suelo durante el balanceo, y premia un patrón de apoyo coordinado. A la vez penaliza el deslizamiento de los pies y los cambios bruscos en las acciones, que es justo lo que hacía la vibración. Se subió también la fricción del suelo y la amortiguación de los servos. Con esto el deslizamiento dejó de ser rentable y apareció una marcha de verdad.

### Cuerpo bajo, pasos cortos y una pata muerta

La marcha funcionaba, pero tenía tres defectos. El cuerpo iba casi pegado al suelo, los pasos eran muy cortos y a veces una pata se quedaba quieta mientras el robot caminaba con las otras tres. Para el cuerpo bajo se añadió un premio por mantener una altura objetivo y se cambió la postura de reposo a una más alta. Para los pasos cortos se subió la altura a la que se premia levantar el pie y se alargó la duración de paso premiada. Para la pata muerta se reforzó el premio al patrón coordinado y se subió la penalización por que unas patas trabajen mucho más que otras.

### Las articulaciones de giro apenas se movían

El siguiente problema fue más sutil. El robot conseguía avanzar moviendo sobre todo los servos de elevación y aprovechando el paralelogramo, pero apenas giraba las patas con los servos de giro. El resultado parecía una cojera, porque la propulsión de verdad de un robot tipo MiniKame viene precisamente de balancear las patas adelante y atrás con esos servos de giro, como si remaran. El robot había encontrado un óptimo tacaño que era eficiente pero feo.

Para arreglarlo se hicieron dos cosas a la vez. Por un lado se añadió un premio explícito al balanceo de las articulaciones, con más peso en las de giro, de forma que mover mucho esos servos suma puntos. Por otro lado se aflojaron las penalizaciones que estaban frenando la amplitud sin darse cuenta, en particular las que castigaban desviarse de la postura de reposo y las que castigaban la velocidad de las articulaciones. También se ampliaron los giros que se ordenan, porque girar obliga sí o sí a usar los servos de giro. Para que esto no reabriera la puerta a la vibración, se subió a la vez la penalización por cambios bruscos de acción, que es la que distingue un balanceo amplio y suave de un temblor rápido.

### Los servos de elevación se movían poco

Después de lo anterior los servos de giro ya hacían recorridos amplios, pero los de elevación se quedaban cortos, lo que se veía claro en el registro de rango por articulación. Se subió su premio al balanceo y se pidió un pie más alto en el premio al despeje, y con eso los servos de elevación pasaron a moverse bastante más, del orden de veinte a treinta y cinco grados por zancada en marcha estable.

### Más velocidad y más variedad

Otro ajuste fue ampliar el rango de velocidades para entrenar marchas más rápidas, hasta unos 0.45 metros por segundo, y modelar un servo más rápido (tipo MG90s) para que el robot pueda alcanzar de verdad esas velocidades.

## Los términos de premio

A continuación se explica qué premia cada término. Los pesos relativos importan tanto como los términos en sí, así que se mencionan.

El premio al seguimiento de velocidad lineal es el principal, con peso 5. Mide cómo de parecida es la velocidad real del robot a la ordenada, usando una campana exponencial: cuanto más se acerca, más premio, llegando al máximo cuando coincide. Tiene además una rampa que da algo más de premio a las velocidades altas, para animar al robot a ir rápido cuando se le pide.

El premio al seguimiento de velocidad de giro, con peso 4, funciona igual pero para la orden de giro. Tiene un peso alto a propósito, porque girar es lo que fuerza a usar los servos de giro y eso ayuda a que las patas hagan recorridos amplios.

El premio al tiempo en el aire, con peso 5, premia que cada pie pase un tiempo razonable en el aire y un tiempo razonable apoyado, en lugar de ir arrastrándose. Es uno de los términos clave para que aparezcan pasos de verdad.

El premio al despeje del pie, con peso 2.0, premia que el pie que está en fase de balanceo se levante hasta una altura objetivo mientras se mueve. Es el término que hace que las patas se levanten de forma visible y no se arrastren rozando el suelo. La altura objetivo se subió a unos cinco centímetros y medio, y el peso se reforzó, precisamente porque las articulaciones de elevación se estaban moviendo poco. Al pedir un pie más alto, esos servos tienen que moverse más.

El premio a la altura del cuerpo, con peso 1, premia mantener el cuerpo cerca de una altura objetivo de unos cinco centímetros. Tiene un peso moderado a propósito, porque sirve para que el robot no vuelva a caminar pegado al suelo, pero sin impedir que el cuerpo oscile o baje un poco cuando hace falta para moverse.

Los premios al balanceo de las articulaciones, uno para los servos de giro con peso 0.2 y otro para los de elevación con peso 0.35, premian mover esas articulaciones con amplitud mientras hay una orden de movimiento. El de elevación se subió respecto a su valor inicial porque esos servos se quedaban demasiado quietos. Llevan un tope para que no se puedan ganar puntos vibrando cada vez más rápido. La clave es que, como la vibración está penalizada por el término de suavidad de acción, lo que más renta es un balanceo amplio y suave, que es exactamente lo que queremos ver.

El premio al patrón de marcha, con peso 10, es el de mayor peso de todos. Premia un trote en diagonal, es decir, que la pata delantera de un lado y la trasera del otro se muevan a la vez, y que ese par vaya en contrafase con el otro par. Esto consigue dos cosas a la vez: una marcha coordinada con sentido visual y que las cuatro patas trabajen, evitando que alguna se quede muerta.

## Los términos de penalización

Las penalizaciones no enseñan a caminar, moldean cómo se camina, recortando los comportamientos feos o peligrosos.

La penalización por terminación, con peso menos 1, resta puntos solo cuando el robot fracasa de verdad (se cae o se inclina demasiado), no cuando el episodio termina por agotar el tiempo. Así se desanima caerse sin castigar el final normal de un episodio.

La penalización por cambios bruscos de acción, con peso menos 1.5, es la que mata la vibración. Mide cuánto cambia la acción de un paso al siguiente y lo penaliza, de modo que un temblor rápido sale muy caro mientras que un movimiento amplio y suave casi no se penaliza.

La penalización por desigualdad en los tiempos de las patas, con peso menos 2, castiga que unas patas pasen mucho más tiempo en el aire o apoyadas que otras. Es la que evita la pata muerta.

La penalización al movimiento del cuerpo, con peso menos 0.5, castiga que el cuerpo suba y baje o cabecee demasiado. Se dejó con un peso bajo a propósito, porque algo de oscilación es normal e incluso necesaria al caminar.

La penalización por inclinación, con peso menos 3, castiga que el cuerpo se incline respecto a la horizontal. Tiene un peso alto porque queremos que el robot se mantenga nivelado y no acabe tumbado.

La penalización por deslizamiento del pie, con peso menos 0.5, castiga que un pie se mueva en horizontal mientras está apoyado en el suelo. Es uno de los frenos directos al truco del cepillo vibrador.

Las penalizaciones a la aceleración, al par y a la velocidad de las articulaciones, todas con pesos muy pequeños, sirven de regularización suave: empujan a un movimiento eficiente y realista sin ahogar la amplitud. La penalización por desviarse de la postura de reposo se dejó casi apagada, con un peso muy pequeño, precisamente para no estorbar a los movimientos amplios que ahora buscamos. Es importante recordar que todas estas penalizaciones de articulación se aplican solo a los ocho servos reales, no a las articulaciones pasivas del paralelogramo, que se mueven solas y a las que no tendría sentido penalizar.

## Una idea para recordar

El diseño funciona porque los premios grandes (seguir la velocidad, dar pasos, levantar el pie, trotar coordinado) empujan al robot a moverse como queremos, mientras que las penalizaciones recortan las salidas fáciles y feas. Cuando algo no sale bien, el primer sitio donde mirar es el equilibrio entre estos pesos. Subir un premio o bajar una penalización suele desbloquear más amplitud, y subir la suavidad o el deslizamiento suele limpiar movimientos sucios.
