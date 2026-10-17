//  Servos:
//
//  | \ ___   ________   ____/ |
//  |(2)___](0)      (1)[___(3)|
//  |__/    |   KAME   |    \__|
//          |          |
//  | \____ |          | ____/ |
//  |(6)___](4)______(5)[___(7)|
//  |__/                    \__|
//               / \
//                |
//           USB  |


#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <ArduinoNvs.h>
#include <kame.h>
#include <config.h>

WebServer server(80);
int calibration[8] = {0, 0, 0, 0, 0, 0, 0, 0};
float position[8] = {90, 90, 90, 90, 90, 90, 90, 90};
Kame robot;


void handleRoot() {
    String html = R"rawliteral(
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <title>Calibration</title>
        <style>
        body {
            background-color: #121212;
            color: #f0f0f0;
            font-family: Arial, sans-serif;
            padding: 20px;
            text-align: center;
        }
        h1 {
            color: #ff3535;
        }
        .servo-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 30px 0;
        }
        .servo-box {
            background: #1e1e1e;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }
        .servo-title {
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .value {
            font-size: 1.5em;
            margin: 10px 0;
        }
        .btn {
            font-size: 1.5em;
            text-decoration: none;
            padding: 8px 14px;
            margin: 5px;
            background: #ff3535;
            color: white;
            border-radius: 8px;
            transition: background 0.3s;
            display: inline-block;
        }
        .btn:hover {
            background: #ff5959;
        }
        .pos-input {
            font-size: 1.1em;
            width: 70px;
            padding: 6px;
            margin: 5px;
            border-radius: 8px;
            border: 1px solid #444;
            background: #2a2a2a;
            color: #f0f0f0;
            text-align: center;
        }
        .current-pos {
            font-size: 1em;
            margin: 8px 0;
            padding: 6px 10px;
            background: #2a2a2a;
            border-radius: 8px;
            color: #ff8c8c;
        }
        h2 {
            color: #ff3535;
            margin-top: 40px;
        }
        pre {
            background: #1e1e1e;
            padding: 10px;
            border-radius: 8px;
            color: #f0f0f0;
            font-size: 1.1em;
        }
        </style>
    </head>
    <body>
        <h1>Calibration</h1>
        <div class="servo-grid">
    )rawliteral";

    for (int i = 0; i < 8; i++) {
        html += "<div class='servo-box'>";
        html += "<div class='servo-title'>Servo " + String(i) + "</div>";
        html += "<a class='btn' href='/increase?i=" + String(i) + "'>&#9650;</a>";
        html += "<div class='value'>" + String(calibration[i]) + "</div>";
        html += "<a class='btn' href='/decrease?i=" + String(i) + "'>&#9660;</a>";
        html += "</div>";
    }

    html += "</div>";
    html += "<a class='btn' href='/load' style='width: 180px; margin: 0 10px;'>Load</a>";
    html += "<a class='btn' href='/save' style='width: 180px; margin: 0 10px;'>Save</a>";

    html += "<h2>Position</h2>";
    html += "<div class='servo-grid'>";
    for (int i = 0; i < 8; i++) {
        html += "<div class='servo-box'>";
        html += "<div class='servo-title'>Servo " + String(i) + "</div>";
        html += "<div class='current-pos'>Current: " + String(position[i], 1) + "&deg;</div>";
        html += "<form action='/setpos' method='get'>";
        html += "<input type='hidden' name='i' value='" + String(i) + "'>";
        html += "<input class='pos-input' type='number' name='pos' min='0' max='180' step='1' value='" + String((int)position[i]) + "'>";
        html += "<br><button class='btn' type='submit'>Set</button>";
        html += "</form>";
        html += "</div>";
    }
    html += "</div>";

    html += R"rawliteral(
        <h3 style="margin-top: 50px;">Generated calibration array</h3>
        <pre>int servo_calibration[8] = {)rawliteral";

    for (int i = 0; i < 8; i++) {
        html += String(calibration[i]);
        if (i < 7) html += ", ";
    }

    html += R"rawliteral(};</pre>
        </body>
        </html>
        )rawliteral";

    server.send(200, "text/html", html);
}

void updateServo(int i){
    if (i >= 0 && i < 8){
        robot.setCalibration(calibration); 
        robot.setServo(i, 90);
    }
}

void handleLoad(){
    if (NVS.begin()){
        for (int i = 0; i < 8; i++){
            calibration[i] = NVS.getInt("servo" + String(i), 0);
            updateServo(i);
        }
    }
    handleRoot();
}

void handleSave(){
    if (NVS.begin()){
        for (int i = 0; i < 8; i++){
            NVS.setInt("servo" + String(i), calibration[i]);
            updateServo(i);
        }
    }
    handleRoot();
}

void handleIncrease(){
    int i = server.arg("i").toInt();
    if (i >= 0 && i < 8){
        calibration[i]++;
        updateServo(i);
    }
    handleRoot();
}

void handleDecrease(){
    int i = server.arg("i").toInt();
    if (i >= 0 && i < 8){
        calibration[i]--;
        updateServo(i);
    }
    handleRoot();
}

void handleSetPos(){
    int i = server.arg("i").toInt();
    float pos = server.arg("pos").toFloat();
    if (i >= 0 && i < 8){
        pos = constrain(pos, 0.0f, 180.0f);
        position[i] = pos;
        robot.setCalibration(calibration);
        robot.setServo(i, pos);
    }
    handleRoot();
}

void setup() {
    Serial.begin(115200);

    WiFi.mode(WIFI_AP);
    WiFi.softAP(SSID, PASSWORD);
    //WiFi.mode(WIFI_STA);
    //WiFi.begin(SSID, PASSWORD);
    MDNS.begin(HOSTNAME);

    robot.init();
    robot.setCalibration(calibration);

    server.on("/", handleRoot);
    server.on("/increase", handleIncrease);
    server.on("/decrease", handleDecrease);
    server.on("/load", handleLoad);
    server.on("/save", handleSave);
    server.on("/setpos", handleSetPos);
    server.begin();
}

void loop() {
    server.handleClient();
}
