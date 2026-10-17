# El robot real

## Componentes

- **Placa:** la PCB propia de Kame32 (`hardware/kame32-JavierIH/pcb/`), con una ESP32 DevKit de 30 pines (tipo DOIT V1) pinchada.
- **Servos:** ocho MG90s. Cuatro giran la pata hacia delante y hacia atrás (giro, eje vertical) y cuatro la suben y bajan (elevación). Cada pata tiene además un paralelogramo pasivo que mantiene el pie perpendicular al suelo. Los MG90s no devuelven su posición: solo se les manda un ángulo.
- **Alimentación:** batería conectada a J5, con interruptor SW1, que da unos +8 V. Dos reguladores (U1 y U3) alimentan los servos en dos grupos de cuatro.
- **IMU:** el diseño original no tiene. Hay una LSM6DS3 comprada (ver más abajo).

## Pines de la ESP32

Sacado del esquema de KiCad (`hardware/kame32-JavierIH/pcb/kame32-pcb/kame32-pcb.net`) y del firmware original (`hardware/kame32-JavierIH/code/lib/Kame/kame.h`).

| Uso | GPIO |
|---|---|
| Servos 0 a 7 | 26, 25, 18, 19, 32, 33, 5, 21 |
| LED | 2 |
| Medida de la tensión de batería (divisor R1/R2 desde +8 V) | 27 |

Conectores de expansión libres en la placa:

| Conector | Pines |
|---|---|
| J7 | GPIO17 (TX2), GPIO16 (RX2), GPIO4, GPIO2 (el del LED), GPIO15 |
| J8 | +8 V, GND, GPIO13, GPIO12, GPIO14 |

Hay pines del DevKit que la placa no conecta a nada: 3V3, GPIO22, GPIO23, GPIO34 y GPIO35 (estos dos últimos solo de entrada). Para usarlos hay que soldar directamente en el pin del módulo.

Cuidado con dos cosas:

- **El pin VIN del DevKit y el pin 1 de J8 llevan +8 V de la batería.** Nunca conectes ahí nada de 3,3 V.
- **No uses el GPIO12 para nada que tenga resistencia pull-up**, como un bus I2C. Es un pin de arranque y la ESP32 dejaría de arrancar.

## La IMU LSM6DS3

Es una placa clónica del modelo de SparkFun, con acelerómetro y giroscopio de tres ejes. Funciona solo a 3,3 V y se daña por encima de unos 3,6 V. Como la ESP32 trabaja a 3,3 V, no hace falta convertidor de nivel.

Conexión prevista por I2C:

| LSM6DS3 | ESP32 |
|---|---|
| VCC | Pin 3V3 del DevKit (soldado en el pin del módulo) |
| GND | J8 pin 2 |
| SDA | GPIO16 (J7, RX2) |
| SCL | GPIO17 (J7, TX2) |

El I2C por defecto de la ESP32 usa el GPIO21, que aquí es un servo, así que hay que indicar los pines al iniciar el bus: `Wire.begin(16, 17)`. La dirección I2C suele ser 0x6B, o 0x6A según el pin SA0. El chip puede ser un LSM6DS3 o un LSM6DS3TR-C: se distingue por el registro de identificación (WHO_AM_I). Se configurará a unos 104–208 Hz con filtro paso bajo, porque la política trabaja a 50 Hz y los servos vibran.

Antes de montarla en el robot hay que probarla suelta: leer su identificación y comprobar que, quieta, la gravedad da alrededor de 1 g y la velocidad de giro alrededor de cero. En el robot debe ir pegada de forma rígida al cuerpo, cerca del centro y alineada con los ejes del robot.

## Pendiente

- Pesar el robot completo y, si se puede, una pata suelta, para corregir las masas del modelo de simulación.
- Confirmar en la placa física que J7 y J8 están accesibles para soldar.
