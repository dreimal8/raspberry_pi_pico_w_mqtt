# Code example for a raspberry pi pico W to send a message via mqtt when a button is pressed


# import
import config
import time
import network
import machine
from umqtt.simple import MQTTClient

# variables
button = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_DOWN)
led_onboard = machine.Pin("LED", machine.Pin.OUT)
led_onboard.off()

# wifi
ssid = config.ssid
password = config.password
    
# mqtt
mqtt_server = config.mqtt_server
client_id = 'picoW'
topic_pub = 'pico_topic'
mqtt_max_reconnect = 5


###########################################################################
#   blink onboard LED
###########################################################################
def blink(count, sleep):
    while count > 0:
        count -= 1
        led_onboard.on()
        time.sleep(sleep)
        led_onboard.off()
        time.sleep(sleep)


###########################################################################
#   connect to wifi
###########################################################################
def wifi_connect():
    
    global wlan
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    # Wait for connect or fail
    max_wait = 10
    print('Waiting for connection', end=" ")
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('.', end=" ")
        blink(1, 0.5)

    print(' ')

    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('Network connection failed')
    else:
        print('Connected')
        status = wlan.ifconfig()
        print( 'ip = ' + status[0] )    


###########################################################################
#   connect to mqtt broker
###########################################################################
def mqtt_connect():
    
    global mqtt_client
    
    mqtt_client = MQTTClient(client_id, mqtt_server, keepalive=3600) # connection will stay up for one hour
    print('Connect to mqtt...')
    mqtt_client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))


###########################################################################
#   if sending mqtt message fails - reconnect here
###########################################################################
def mqtt_reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    mqtt_max_reconnect -= 1
    blink(5, 0.1)
    time.sleep(0.5)
    mqtt_connect()


###########################################################################
#   send mqtt message, reconnect if necessary
###########################################################################
def sendMqtt(topic_msg):
    
    global mqtt_client
    global mqtt_max_reconnect
    
    if wlan.status() == 3:
        print('mqtt start - try to send...')
        try:
            mqtt_client.check_msg() # to check if mqtt connection is still alive
            mqtt_client.publish(topic_pub, topic_msg)
            print('Message sent: \"' + topic_msg + "\"")
            mqtt_max_reconnect = 5
            blink(2, 0.2)
        except OSError as e:
            if mqtt_max_reconnect > 0:
                mqtt_reconnect()
                sendMqtt(topic_msg) # after reconnect - send again!
            else:
                time.sleep(5)
                machine.reset()
    else:
        print('No wifi')


###########################################################################
#   M A I N
###########################################################################
wifi_connect()
mqtt_connect()



while True:
    if button.value() == 1:
        print('Button detected!')
        print('wlan status: ' + str(wlan.status()))
        if wlan.status() != 3:
            wifi_connect()
        sendMqtt('alive')
        time.sleep(2)
        blink(1, 0.2)

