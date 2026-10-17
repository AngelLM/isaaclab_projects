# El modelo de simulación

El robot está descrito en `modelo/usd/kame32.usd`. Este documento explica cómo está construido, según la revisión que se hizo en octubre de 2026 abriendo el archivo.

## De dónde sale

Piezas de FreeCAD (`hardware/kame32-JavierIH/3d/`), pasadas a Blender (`modelo/blender/kame32.blend`) y exportadas como STL (`modelo/stl/`). Con esas piezas se montó el robot en Isaac Sim. Las versiones intermedias están en `archivo/usd-iteraciones/`.

## Cuerpos

Hay 17 cuerpos rígidos, todos con colisión: el cuerpo central (`Body`) y, por cada pata, un `Bracket` (el soporte que gira), un `Leg` (la pata), un `Link` (la barra del paralelogramo) y un `Foot` (el pie). Los nombres de las patas son `LeftFront`, `RightFront`, `LeftBack` y `RightBack`.

## Juntas de cada pata

```
Body ──(giro, eje Z, SERVO)──► Bracket ──(elevación, eje X, SERVO)──► Leg ──(libre)──► Foot
                                  │                                                     ▲
                                  └──(libre, cierre de lazo)──► Link ──(libre)──────────┘
```

- **Giro** (`Body_B**`): servo, eje vertical. Límites de −25° a 90° o de −90° a 25° según la pata, reflejados entre izquierda y derecha.
- **Elevación** (`B**_L**`): servo, eje X. Límites de −60° a 75° en la izquierda y de −75° a 60° en la derecha.
- **Leg→Foot y Link→Foot**: libres, sin motor.
- **Bracket→Link** (`B**_Lk**`): libre y marcada como *excluida de la articulación*. Es la que cierra el lazo del paralelogramo. PhysX no puede simular lazos cerrados dentro de una articulación, así que una junta del lazo tiene que quedar fuera y resolverse aparte. Así está bien hecho.

En total la articulación tiene 16 grados de libertad, de los cuales solo 8 tienen motor. La raíz de la articulación es `Body`. Los motores del USD (rigidez 10, amortiguación 1) se sustituyen en Isaac Lab por la configuración de actuador del entrenamiento.

## Masas

| Pieza | Masa | Cantidad |
|---|---|---|
| Body | 110 g | 1 |
| Bracket | 25 g | 4 |
| Leg, Link, Foot | 10 g | 12 |
| **Total** | **330 g** | |

Son estimaciones redondas. Solo los ocho MG90s pesan unos 107 g (13,4 g cada uno), a lo que hay que sumar la batería, la ESP32 y la placa, así que el robot real probablemente pesa más. Hay que pesarlo y corregirlo, porque la masa influye mucho en cómo camina en simulación.

## Detalles menores

- La junta de giro delantera izquierda (`Body_BLF`) tiene un descuadre de 0,5 mm en Z en su anclaje con el bracket; las otras tres tienen cero. No afecta en la práctica, pero se puede corregir.
- El archivo declara estar en centímetros (`metersPerUnit = 0.01`), pero sus medidas están en metros: el robot ocupa unos 10 × 21,6 × 5,6 cm. Isaac Lab lo carga bien, pero puede confundir si se abre en otra herramienta.
- La ruta del USD tiene que pasarse a Isaac Lab como texto (`str`), no como objeto `Path`, o falla al cargar.
- La postura con todas las juntas a cero es una postura de pie estable, con el cuerpo a unos 3 cm del suelo.
