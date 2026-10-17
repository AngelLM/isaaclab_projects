// kame32 control sketch driven by the trained RL policy (no-IMU variant).
//
// This keeps the WiFi access point, the web page and the joystick from the original gamepad
// sketch, but replaces the oscillator gait with neural-network inference: every 20 ms (50 Hz)
// the joystick is turned into a velocity command, the policy produces 8 joint targets, and those
// are written to the servos. The animation buttons (A..Z) still call the built-in Kame routines.
//
// Build this sketch with the "policy" PlatformIO environment (see platformio.ini).

#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <config.h>
#include <kame.h>
#include <gamepad.h>
#include <policy.h>

Kame robot;
WebServer server(80);
Policy policy;

int joy_x = 0;   // -100..100, left/right  (turn)
int joy_y = 0;   // -100..100, back/forward (advance)

unsigned long last_tick = 0;
const unsigned long CONTROL_PERIOD_MS = 20;  // 50 Hz, matches the training control rate

// Velocity command ranges the policy was trained with.
const float LIN_FWD_MAX = 0.45f;   // m/s forward  (joy_y = +100)
const float LIN_BACK_MAX = 0.15f;  // m/s backward (joy_y = -100)
const float ANG_MAX = 1.0f;        // rad/s turn   (joy_x = +-100)


void handleRoot() {
    server.send(200, "text/html", gamepad_html);
}

void handleJoystick() {
    if (server.hasArg("x") && server.hasArg("y")) {
        joy_x = server.arg("x").toInt();
        joy_y = server.arg("y").toInt();
        server.send(200, "text/plain", "OK");
    } else {
        server.send(400, "text/plain", "Missing x or y");
    }
}

void handleButton() {
    if (server.hasArg("label")) {
        String label = server.arg("label");
        Serial.println(label);
        if (label == "A") {
            robot.hello();
        } else if (label == "B") {
            robot.jump();
        } else if (label == "C") {
            robot.pushUp(4, 1000);
        } else if (label == "X") {
            robot.dance(2, 1000);
        } else if (label == "Y") {
            robot.moonwalkL(2, 2000);
        } else if (label == "Z") {
            robot.frontBack(2, 1000);
        } else if (label == "Start") {
            robot.arm();
        } else if (label == "Stop") {
            robot.disarm();
        } else {
            Serial.println("Unknown button: " + label);
        }
        server.send(200, "text/plain", "Button OK");
    } else {
        server.send(400, "text/plain", "Missing label");
    }
}


void setup() {
    Serial.begin(115200);

    WiFi.mode(WIFI_AP);
    WiFi.softAP(SSID, PASSWORD);
    MDNS.begin(HOSTNAME);

    robot.init();
    robot.home();

    policy.begin();
    if (policy.selfTest())
        Serial.println("[policy] self-test OK: C inference matches the exported reference.");
    else
        Serial.println("[policy] self-test FAILED: check policy_weights.h / re-run export_policy.py.");

    server.on("/", handleRoot);
    server.on("/joystick", handleJoystick);
    server.on("/button", handleButton);
    server.begin();
}


// Map the joystick to the velocity command the policy expects.
void joystickToCommand(float &lin_vel_x, float &lin_vel_y, float &ang_vel_z) {
    float fy = joy_y / 100.0f;   // -1..1, forward positive
    float fx = joy_x / 100.0f;   // -1..1, right positive
    lin_vel_x = (fy >= 0.0f) ? fy * LIN_FWD_MAX : fy * LIN_BACK_MAX;
    lin_vel_y = 0.0f;            // the robot was not trained to strafe
    ang_vel_z = fx * ANG_MAX;    // if it turns the wrong way, flip the sign here
}


void loop() {
    server.handleClient();

    unsigned long now = millis();
    if (now - last_tick < CONTROL_PERIOD_MS) return;
    last_tick = now;

    float lin_vel_x, lin_vel_y, ang_vel_z;
    joystickToCommand(lin_vel_x, lin_vel_y, ang_vel_z);

    float servo_deg[8];
    policy.step(lin_vel_x, lin_vel_y, ang_vel_z, servo_deg);

    for (int i = 0; i < 8; i++)
        robot.setServo(i, servo_deg[i]);
}
