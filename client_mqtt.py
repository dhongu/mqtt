# coding=utf-8


import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import MFRC522
import signal

STATUS_TOPIC = 'rc522/01/status'
EVENT_TOPIC = 'rc522/01'
HOST = "localhost"
PORT = 1883

continue_reading = True


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    print("Ctrl+C captured, ending read.")
    continue_reading = False
    GPIO.cleanup()


def mqtt_on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))
    try:
        controller_name, reader_code, card = msg.topic.split('/')
        if 'granted' in msg:
            print ('granted for card %s' % card )
    except:
        pass


def mqtt_init():
    client_id = 'rc522'
    client = mqtt.Client()
    client.on_message = mqtt_on_message
    return client


def main():
    global continue_reading
    continue_reading = True
    client = mqtt_init()
    client.connect("192.168.0.3", 1883, 60)

    client.loop_start()
    print("RFID is ready")
    client.publish(STATUS_TOPIC, "rc522 is online", qos=1, retain=True)
    MIFAREReader = MFRC522.MFRC522()
    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    while continue_reading:
        try:
            # Scan for cards
            (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

            # If a card is found
            if status == MIFAREReader.MI_OK:
                print("Card detected")

            # Get the UID of the card
            (status, uid) = MIFAREReader.MFRC522_Anticoll()
            # If we have the UID, continue
            if status == MIFAREReader.MI_OK:
                card = " ".join(["{:02x}".format(x) for x in uid])
                print("Card read UID: %s " % card)
                client.publish(EVENT_TOPIC, '{"card_code":"%s"}' % card )
                client.subscribe(EVENT_TOPIC+'/'+card)
        except KeyboardInterrupt:
            print("End")
            continue_reading = False

    client.publish(STATUS_TOPIC, "rc522 dead", qos=1, retain=True)
    client.loop_stop()
    client.disconnect()
    GPIO.cleanup()


if __name__ == "__main__":
    main()
