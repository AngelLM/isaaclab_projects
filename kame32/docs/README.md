# Documentación del entrenamiento de kame32

Esta carpeta explica cómo está montado el entrenamiento por refuerzo del robot kame32 en Isaac Lab, qué decisiones se han tomado y por qué, y cómo usarlo y ajustarlo. La idea es que cualquiera que abra el proyecto dentro de unos meses (tú incluido) entienda no solo qué hace cada cosa, sino el motivo de que esté así.

## Qué es esto en una frase

kame32 es un robot cuadrúpedo tipo araña, pequeño y barato, y aquí se entrena con aprendizaje por refuerzo (en concreto con PPO) para que aprenda a caminar y a girar siguiendo un comando de velocidad, dentro de un simulador físico que ejecuta miles de copias del robot a la vez.

## El objetivo

Queremos que el robot aprenda una marcha que tenga sentido visual, es decir, que mueva las cuatro patas de forma coordinada y con recorridos amplios, no que avance a base de microvibraciones o arrastrándose. Además queremos que sepa ir a distintas velocidades, desde muy despacio hasta unos 0.45 metros por segundo, y que sepa girar a izquierda y derecha.

## Cómo está organizada la documentación

El documento "01-el-robot-kame32.md" describe el robot en sí, su mecánica, sus articulaciones y cómo está modelado en el archivo USD que carga el simulador. Es importante leerlo primero porque casi todas las decisiones posteriores dependen de cómo es el robot.

El documento "02-el-entorno-rl.md" describe el entorno de aprendizaje, es decir, qué ve el robot (las observaciones), qué puede hacer (las acciones), cómo se le dan las órdenes (los comandos), cómo se le añade variedad para que sea robusto (la aleatorización) y los parámetros de la simulación.

El documento "03-recompensas.md" es el corazón del proyecto. Explica cada término de recompensa, qué comportamiento premia o castiga y, sobre todo, qué problema concreto vino a resolver. Aquí está contada la historia de los fallos que fueron apareciendo y cómo se corrigieron.

El documento "04-uso-y-ajuste.md" es la parte práctica. Explica cómo instalar, entrenar, reproducir una política ya entrenada, grabar vídeo y medir cuánto se mueve cada articulación. También recoge las perillas de ajuste más útiles y las notas para un futuro paso al robot real.

## Resumen muy rápido del montaje

El robot tiene ocho servos de verdad (dos por pata) y un mecanismo de paralelogramo pasivo que mantiene el pie horizontal. El entrenamiento usa el flujo de trabajo de tareas basadas en managers de Isaac Lab, copiando el esquema de la tarea de locomoción por velocidad que trae Isaac Lab para robots como el ANYmal o el Spot, pero adaptado al tamaño y a la mecánica de kame32. El algoritmo es PPO a través de la librería skrl. Los registros de cada entrenamiento se guardan en la carpeta "logs/skrl/kame32_walk".
