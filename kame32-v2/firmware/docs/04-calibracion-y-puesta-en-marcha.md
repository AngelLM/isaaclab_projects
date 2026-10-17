# Calibración y puesta en marcha

Este es el documento más práctico. Explica cómo poner el robot en marcha con seguridad y, sobre todo, cómo ajustar el único punto que casi seguro necesita ajuste, que es el sentido de giro de cada servo. Tómatelo con calma y hazlo con el robot sujeto, no en el suelo, hasta que veas que se mueve con sentido.

## Primero, la seguridad

Antes de dejar el robot en el suelo, sujétalo en el aire o ponlo sobre un soporte de forma que las patas no toquen nada y puedan moverse libremente. Esto es importante porque, si algún servo está montado al revés respecto a la simulación, la primera vez la pata se moverá en el sentido equivocado, y no quieres que eso pase con el peso del robot encima ni con las patas trabadas contra el suelo. Ten también a mano el botón de parada de la web, que desactiva los servos.

## Por qué hace falta calibrar el sentido

En la simulación, cada articulación tiene un sentido positivo definido por el modelo. En el robot real, cada servo está montado físicamente de una manera, y su sentido positivo puede coincidir o no con el de la simulación. Cuando no coincide, la pata se mueve justo al revés de lo que la política pretende, y el robot no camina aunque la red esté perfecta. Esto no es un error, es simplemente la realidad de montar servos, y por eso hay un ajuste previsto para ello.

En el código de la librería de la política, en el archivo policy.cpp, hay una lista de ocho números, uno por servo físico, que valen más uno o menos uno. Esa lista se llama el array de sentidos. Un más uno significa que el servo gira en el mismo sentido que la simulación, y un menos uno significa que gira al revés y hay que invertirlo. De fábrica están todos a más uno, que es la hipótesis de partida, pero es normal que varios haya que ponerlos a menos uno.

## Cómo averiguar el sentido de cada servo

La forma más segura es ir servo por servo. Con el robot sujeto en el aire y los servos activados, mueve el joystick despacio hacia delante y observa. Fíjate en cada pata y compara lo que hace con lo que debería hacer para caminar hacia delante. Si una articulación se mueve claramente en el sentido contrario al que tendría sentido, apunta ese servo. Cuando tengas identificados los servos que van al revés, edita el array de sentidos en policy.cpp y pon a menos uno los que correspondan, deja a más uno los demás, vuelve a compilar y a subir, y prueba otra vez.

Conviene saber qué servo es cada uno para no confundirse. Los índices de servo del robot son estos. El cero es la cadera delantera izquierda, el uno la cadera delantera derecha, el dos la elevación delantera izquierda, el tres la elevación delantera derecha, el cuatro la cadera trasera izquierda, el cinco la cadera trasera derecha, el seis la elevación trasera izquierda y el siete la elevación trasera derecha. Las caderas son los servos que giran la pata en horizontal, y las elevaciones son los que suben y bajan la pata.

Es probable que tengas que dar dos o tres vueltas a este proceso hasta que las cuatro patas se muevan de forma coordinada. No te desanimes, es lo normal. Una pista útil es que las patas del mismo lado suelen compartir el sentido, así que si inviertes una, mira si su compañera del mismo lado también lo necesita.

## El sentido del giro

Además del sentido de cada servo, está el sentido del giro completo del robot. Si al empujar el joystick a la derecha el robot gira a la izquierda, o al revés, no es un problema de servos sino del signo del comando de giro. Eso se corrige en el archivo del sketch, en la función que convierte el joystick en comando, cambiando el signo de la velocidad de giro. Es un cambio de una línea.

## La postura de reposo

Cuando el joystick está en el centro, la política recibe un comando cero y se queda quieta en su postura de reposo. Esa postura debería parecerse a la postura de pie neutra del robot, la misma que usaba el firmware original al quedarse quieto. Si ves que la postura de reposo con la política queda muy distinta de la de pie normal, con las patas demasiado abiertas o demasiado cerradas, puede ser una pista de que algún servo tiene el sentido cambiado o de que la calibración de ceros del propio robot, la que se hace con la herramienta de calibración original, necesita un repaso. Merece la pena tener bien calibrados los ceros de los servos con la herramienta original antes de pelearse con la política.

## Interpretar el joystick

El eje de adelante y atrás del joystick controla la velocidad hacia delante. Hacia delante del todo pide la velocidad máxima que se entrenó, y hacia atrás pide marcha atrás, más lenta. El eje de izquierda y derecha controla el giro. Se pueden combinar los dos, es decir, avanzar girando, y la política lo gestiona. En el centro, el robot se queda quieto.

## Cuando ya camina en el aire

Cuando veas que, sujeto en el aire, las cuatro patas hacen un movimiento de caminar coordinado y en el sentido correcto al pedirle ir hacia delante, entonces ya puedes probarlo en el suelo, en una superficie plana, lisa y con algo de agarre. Empieza con velocidades bajas. A partir de ahí es cuestión de probar y observar, y de leer el documento de limitaciones para entender qué esperar.
