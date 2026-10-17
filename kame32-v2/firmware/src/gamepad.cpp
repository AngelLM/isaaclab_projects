// Firmware original de Kame32 (marcha por osciladores + joystick web), sin modificar.
// El código vive en el submódulo de JavierIH; aquí solo se incluye para compilarlo con el
// config.h de este robot (src/config.h, con su calibración de servos).
// PlatformIO no sigue el #include de abajo para descubrir librerías, así que se nombran aquí.
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <kame.h>

#include "../../hardware/kame32-JavierIH/code/src/gamepad.cpp"
