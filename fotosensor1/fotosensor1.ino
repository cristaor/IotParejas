int dht_dpin = 0;
const long A = 1000;     //Resistencia en oscuridad en KΩ
const int B = 15;        //Resistencia a la luz (10 Lux) en KΩ

#define LED D1 // LED

//Esta funcion aplica la formula para obtener la intensidad luminica
double getLightIntensity(int analogValue, int resistanceValue)
{
  //double VoltageOut = analogValue*0.0048828125;
  //int luxValue = ((2500/VoltageOut-500)/resistanceValue);
  int luxValue = ((long)analogValue*A*10)/((long)B*resistanceValue*(1024-analogValue));
  return luxValue;
}


void setup()
{
 Serial.begin(9600);
 pinMode(LED, OUTPUT);
 digitalWrite(LED, LOW); //LED comienza apagado
}

void loop()
{
       int lectura = analogRead(dht_dpin);
       int resistencia = 10; //we are using a 10K ohms resistor
   
       Serial.print("Current Ligth Intensity = ");
       Serial.print(getLightIntensity(lectura, resistencia));
       Serial.println(" lux");
       delay(1000);
}
