#include <ArduinoJson.h>
#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>

// Flotador
#define PIN_FLOT A0  
float combustible = 0;
unsigned long last_read = 0;

// Generador
#define PIN_ON 8
#define PIN_OFF 7
#define PIN_MOT 4
#define PIN_ST 2
unsigned long tiempo = 0, tx = 0;
const unsigned long TST = 5000;  
bool generadorEncendido = false, partidaActiva = false;

// LAN
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };  
IPAddress ip(192, 168, 0, 156);
IPAddress mqtt_server(192, 168, 0, 112);             
EthernetServer server(80);
EthernetClient ethClient;
PubSubClient client(ethClient);                
char contenido[100] = ""; 
char state[10] = "Apagado";

void callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Mensaje recibido en el tópico: ");
    Serial.println(topic);

    // Convertir el payload a String
    String message = "";
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    Serial.println("Mensaje: " + message);

    // Analizar JSON
    StaticJsonDocument<200> jsonDoc;
    DeserializationError error = deserializeJson(jsonDoc, message);
    
    if (error) {
        Serial.println("Error al parsear JSON");
        return;
    }

    // Obtener los valores del JSON
    const char* id_sensor = jsonDoc["id_sensor"];
    int estado = jsonDoc["estado"];

    Serial.print("ID Sensor: "); Serial.println(id_sensor);
    Serial.print("Estado: "); Serial.println(estado);

    // Encender o apagar el generador según el estado recibido
    if (estado == 1) {
        iniciarGenerador();
    } else if (estado == 0) {
        apagarGenerador();
    }
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("Intentando conectar a MQTT...");
        if (client.connect("ArduinoEthernetClient")) {
            Serial.println(" ¡Conectado a MQTT!");
            client.subscribe("generador/control");  // Suscribirse al tópico de control
        } else {
            Serial.print("Error, rc=");
            Serial.println(client.state());
            Serial.println("Reintentando en 5 segundos...");
            delay(5000);
        }
    }
}

void setup() {
  pinMode(PIN_FLOT, INPUT);  
  analogReference(INTERNAL);
  pinMode(PIN_ON, INPUT);
  pinMode(PIN_OFF, INPUT);
  pinMode(PIN_ST, OUTPUT);
  pinMode(PIN_MOT, OUTPUT);
  digitalWrite(PIN_ST, LOW);
  digitalWrite(PIN_MOT, LOW);
  
  Serial.begin(9600);
  Ethernet.begin(mac, ip);
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    Serial.println(F("Ethernet shield no presente :("));
    while (true) {}
  }
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println(F("Cable Ethernet desconectado o defectuoso."));
  }
  server.begin();
  Serial.println(F("Servidor iniciado, esperando conexiones..."));
  Serial.print("Servidor HTTP iniciado en: ");
  Serial.println(Ethernet.localIP());

      // Configurar MQTT
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

    // Intentar conectar a MQTT
  reconnect();
}

void loop() {
  tiempo = millis();

  if (!client.connected()) {
        reconnect();
  }
  client.loop();
  
  if (millis() - last_read > 5000) {
    int binflot = analogRead(PIN_FLOT);
    combustible = 100.0 * binflot / 1023;
    last_read = millis();
    Serial.print(F("Combustible: ")); Serial.println(combustible, 1);
    enviarCombustibleMQTT();
  }
  //delay(100);
  //solicitudUpdate();

  if (digitalRead(PIN_ON) == HIGH && !generadorEncendido) {
    iniciarGenerador();
  }

  if (partidaActiva && (tiempo - tx >= TST)) {
    partidaActiva = false;
    digitalWrite(PIN_ST, LOW);
    Serial.println(F("Motor de partida apagado"));
  }

  if (digitalRead(PIN_OFF) == HIGH) {
    apagarGenerador();
  }
}

void iniciarGenerador() {
  generadorEncendido = true;
  partidaActiva = true;
  tx = tiempo;
  strcpy(state, "Encendido");
  digitalWrite(PIN_ST, HIGH);
  digitalWrite(PIN_MOT, HIGH);
  Serial.println(F("Generador encendido"));
}

void apagarGenerador() {
  generadorEncendido = false;
  partidaActiva = false;
  strcpy(state, "Apagado");
  digitalWrite(PIN_ST, LOW);
  digitalWrite(PIN_MOT, LOW);
  Serial.println(F("Generador apagado"));
}

void enviarCombustibleMQTT() {
    StaticJsonDocument<200> jsonDoc;
    String macStr = "";
    for (int i = 0; i < 6; i++) {
        macStr += String(mac[i], HEX);
        if (i < 5) macStr += ":";
    }

    char combustibleStr[10];  
    dtostrf(combustible, 6, 2, combustibleStr);  // (valor, ancho mínimo, decimales, destino)

    jsonDoc["id_sensor"] = macStr;
    jsonDoc["combustible"] = atof(combustibleStr);  // Convertir string a float con 2 decimales
    jsonDoc["estado"] = generadorEncendido;

    char buffer[256];
    serializeJson(jsonDoc, buffer);
    client.publish("generador/combustible", buffer);

    Serial.print("Enviado a MQTT: ");
    Serial.println(buffer);
}