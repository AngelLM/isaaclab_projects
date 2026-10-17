# Limitaciones y qué esperar

Este documento es una explicación honesta de qué puedes esperar de este montaje y qué no. Llevar una política de refuerzo de la simulación a un robot real es un salto que casi nunca sale perfecto a la primera, y conviene saberlo para no frustrarse y para saber dónde mirar cuando algo no va.

## El salto de la simulación al mundo real

La política aprendió a caminar en un simulador físico. Un simulador es una aproximación del mundo real, buena pero aproximación al fin y al cabo. En el simulador, el suelo, la fricción, el peso de las piezas, la fuerza de los servos y su velocidad de respuesta son valores concretos que pueden no coincidir del todo con los del robot de verdad. Esta diferencia entre la simulación y la realidad es el motivo principal de que una marcha que se ve perfecta en pantalla pueda salir regular en el robot. No es un fallo del trabajo, es la naturaleza del problema, y tiene solución a base de ajustar y, si hace falta, reentrenar.

## Esta política es ciega

La política que hemos desplegado no tiene ningún sensor. No siente la inclinación del cuerpo ni la velocidad de giro, porque decidimos no depender de una unidad inercial. Esto tiene una consecuencia importante: la política no puede reaccionar a lo que no percibe. Reproduce un patrón de marcha aprendido, como quien repite unos pasos de memoria, pero si el robot tropieza, si el suelo tiene un desnivel o si alguien lo empuja, la política no se entera y no corrige. En simulación, en suelo plano y sin sorpresas, esto funciona bien, pero en el mundo real la falta de reacción se nota, sobre todo en superficies que no sean lisas y planas.

Si más adelante decides montar una unidad inercial en el robot, existe la otra política que entrenamos, la que sí usa ese sensor, y que es capaz de reaccionar a empujones y desniveles. Pasar a esa política requeriría añadir el sensor, leerlo en el firmware e incorporarlo a la observación, pero el camino está preparado y sería una mejora grande en robustez.

## Los servos reales

En la simulación modelamos un servo rápido, del tipo MG90s. Si tu robot monta servos más lentos o más débiles, como los SG90 más básicos, puede que no sean capaces de seguir los movimientos que la política pide a la velocidad a la que los pide, y la marcha saldrá más torpe. Si ves que las patas van siempre por detrás de lo que deberían, o que el robot se arrastra en lugar de dar pasos limpios, puede ser cosa de los servos. Una opción es reentrenar la política modelando el servo real más despacio, para que aprenda una marcha que el servo sí pueda ejecutar.

## Los ceros y los sentidos

Como se explica en el documento de calibración, el sentido de cada servo y la correspondencia de la postura de reposo son cosas que casi seguro hay que ajustar a mano. Si el robot no camina, lo primero que hay que descartar no es la red, que ya está verificada, sino esta parte física. Ten paciencia con la calibración de sentidos, que es donde se resuelven la mayoría de los problemas de las primeras pruebas.

## Qué es un buen resultado

Un buen resultado en esta primera fase es que el robot, en el suelo plano y a velocidad baja, avance de forma más o menos estable moviendo las cuatro patas de manera coordinada, y que responda al joystick al pedirle ir más rápido, más despacio o girar. No esperes que suba escalones, que ande por terreno irregular o que aguante un empujón fuerte, porque para eso haría falta la unidad inercial y probablemente más entrenamiento. Si consigues una marcha decente en suelo plano controlada con el joystick, el experimento ha salido bien.

## El camino de mejora

Si quieres ir más allá, el orden natural de las mejoras sería este. Primero, afinar la calibración de servos y la correspondencia de la postura de reposo, que es lo más barato y lo que más suele mejorar. Segundo, si los servos reales se quedan cortos, reentrenar modelando el servo real. Tercero, si necesitas robustez de verdad, montar la unidad inercial y pasar a la política reactiva. Cada uno de estos pasos es una mejora clara sobre el anterior.
