# Entrenamiento (desde cero)

Aquí irá el proyecto de entrenamiento nuevo de Isaac Lab, que se construirá paso a paso y documentando cada decisión. Todavía está vacío.

Punto de partida acordado:

- Robot: `../modelo/usd/kame32.usd`, con las masas corregidas cuando se pese el robot real.
- Servos: MG90s.
- Observaciones de la política: solo lo que el robot real puede medir, es decir, la IMU LSM6DS3 (velocidad de giro y orientación), el comando de velocidad y las últimas órdenes a los servos.
- Sensores de contacto: solo para recompensas y para detectar caídas.

Antes de empezar, conviene leer `../docs/03-lecciones-aprendidas.md`.
