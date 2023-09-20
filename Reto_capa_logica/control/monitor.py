from argparse import ArgumentError
import ssl
from django.db.models import Avg
from datetime import timedelta, datetime
from receiver.models import Data, Measurement, Station
import paho.mqtt.client as mqtt
import schedule
import time
from django.conf import settings

client = mqtt.Client(settings.MQTT_USER_PUB)


def analyze_data():
    # Consulta todos los datos de la última hora, los agrupa por estación y variable
    # Compara cada valor con respecto al valor máximo definido en la tabla receiver_measurement
    # Si el valor esta por encima del máximo lo va sumando a una medición
    # Luego calcula el porcentaje de datos por encima del máximo versus la muestra de la última hora
    #  Si el porcentaje supera el 20% se envía una alerta al dispositivo

    print("Calculando alertas...")
    measurements = Measurement.objects.all()
    stations = Station.objects.all()
    alerts=0
    count_stations=0
    valores_mayores=0
    locations = Location.objects.all()
    countries= Country.objects.all()
    states = State.objects.all()
    cities = City.objects.all()
    users=User.objects.all()

    for station in stations:
        #print(" Location " + str(station.location.id))
        location=locations.filter(id=station.location.id).first()
        #print(str(location.id))
        #print(str(location.id))
        country=countries.filter(id=location.country.id).values()[0]["name"]
        state=State.objects.filter(id=location.state.id).values()[0]["name"]
        city=City.objects.filter(id=location.city.id).values()[0]["name"]
        user=User.objects.filter(id=station.user_id).values()[0]["username"]
        count_stations +=1
        print("Valores recibidos {},{},{},{}",country,state,city,user)

        for measurement in measurements:
            tam_lista=1
            valores_mayores=0
            stationData = Data.objects.filter(station__id=station.id, measurement__name=measurement.name,base_time__gte=datetime.now() - timedelta(minutes=60)).values("values")
            #aux = stationData.select()
            for item in stationData.iterator():
                #print(item)
                print(type(item))
                for keys in item:
                    #print(item[keys])
                    print(type(item[keys]))
                    for valor in item[keys]:
                        tam_lista += 1
                        if valor > measurement.max_value :
                            valores_mayores += 1
            porcentaje_valores=round((valores_mayores/tam_lista)*100,0)
            print("Estacion No " + str(station.id) + "::::Variable: " + measurement.name + ":::: Porcentaje mayres" + str(porcentaje_valores) + " ::::Tamano Listas: " + str(tam_lista) )

            alert = False

            if porcentaje_valores > 20:
                alert = True

            if alert:
                message = "ALERT {} {} {}".format(measurement.name, tam_lista, porcentaje_valores)
                topic = '{}/{}/{}/{}/in'.format(country, state, city, user)
                print(datetime.now(), "Sending alert to {} {}".format(topic, measurement.name))
                client.publish(topic, message)
                alerts += 1
    print (count_stations, "estaciones revisadas")
    print(alerts, "alertas enviadas")

def on_connect(client, userdata, flags, rc):
    '''
    Función que se ejecuta cuando se conecta al bróker.
    '''
    print("Conectando al broker MQTT...", mqtt.connack_string(rc))


def on_disconnect(client: mqtt.Client, userdata, rc):
    '''
    Función que se ejecuta cuando se desconecta del broker.
    Intenta reconectar al bróker.
    '''
    print("Desconectado con mensaje:" + str(mqtt.connack_string(rc)))
    print("Reconectando...")
    client.reconnect()


def setup_mqtt():
    '''
    Configura el cliente MQTT para conectarse al broker.
    '''

    print("Iniciando cliente MQTT...", settings.MQTT_HOST, settings.MQTT_PORT)
    global client
    try:
        client = mqtt.Client(settings.MQTT_USER_PUB)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        if settings.MQTT_USE_TLS:
            client.tls_set(ca_certs=settings.CA_CRT_PATH,
                           tls_version=ssl.PROTOCOL_TLSv1_2, cert_reqs=ssl.CERT_NONE)

        client.username_pw_set(settings.MQTT_USER_PUB,
                               settings.MQTT_PASSWORD_PUB)
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT)

    except Exception as e:
        print('Ocurrió un error al conectar con el bróker MQTT:', e)


def start_cron():
    '''
    Inicia el cron que se encarga de ejecutar la función analyze_data cada minuto.
    '''
    print("Iniciando cron...")
    schedule.every().hour.do(analyze_data)
    print("Servicio de control iniciado")
    while 1:
        schedule.run_pending()
        time.sleep(1)
