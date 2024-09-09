#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ArduinoJson.h>
#include <TaskScheduler.h>

#define WIFI_SSID "bokya"
#define WIFI_PASSWORD "chicksilog"
#define SERVER_URL "ccscloud.dlsu.edu.ph"
#define PORT 20281


#define SS_PIN  5  // ESP32 pin GPIO5 
#define RST_PIN 27 // ESP32 pin GPIO27 
#define LED_PIN 22

MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;

Scheduler scheduler;

void collectData();  // Forward declaration of the collectData function

Task taskCollectData(5000, TASK_FOREVER, &collectData);

WiFiClient client;


void setup() {
  Serial.begin(9600);
  SPI.begin(); // init SPI bus
  rfid.PCD_Init(); // init MFRC522

  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }

  pinMode(LED_PIN, OUTPUT);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  Serial.println("Tap an RFID/NFC tag on the RFID-RC522 reader");

  scheduler.addTask(taskCollectData);
  taskCollectData.enable();
}

void loop() {
  scheduler.execute();
}

void collectData() {
  if (client.connect(SERVER_URL, PORT)) {
    while(true){
      if (rfid.PICC_IsNewCardPresent()) { // new tag is available
        if (rfid.PICC_ReadCardSerial()) { // NUID has been readed
          MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
          if (piccType != MFRC522::PICC_TYPE_MIFARE_MINI &&
              piccType != MFRC522::PICC_TYPE_MIFARE_1K &&
              piccType != MFRC522::PICC_TYPE_MIFARE_4K) {
            Serial.println(F("This sample only works with MIFARE Classic cards."));
            return;
          }

          String rfid_uid = "";
          for (byte i = 0; i < rfid.uid.size; i++) {
            rfid_uid += String(rfid.uid.uidByte[i], HEX);
            if (i < rfid.uid.size - 1) {
              rfid_uid += " ";
            }
          }

          String terminal_id = "Terminal_1";
          String timestamp = String(millis());

          StaticJsonDocument<200> doc;
          doc["rfid_uid"] = rfid_uid;
          doc["type"] = piccType;
          doc["terminal_id"] = terminal_id;
          doc["timestamp"] = timestamp;

          String json;
          serializeJson(doc, json);

          Serial.print("Sending JSON: ");
          Serial.println(json);  // Debugging statement

          digitalWrite(LED_PIN, HIGH);
          delay(1000);
          digitalWrite(LED_PIN, LOW);

          client.print(json);  // Ensure the entire JSON string is sent
          // client.stop();

          rfid.PICC_HaltA(); // halt PICC
          rfid.PCD_StopCrypto1(); // stop encryption on PCD
        }
      }
    }
  }
}
