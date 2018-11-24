# coding=utf-8


import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import MFRC522
import signal

STATUS_TOPIC = 'rc522/status'
EVENT_TOPIC = 'rc522/events'
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
    client.subscribe('test')

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
                client.reconnect()
                client.publish(STATUS_TOPIC, "rc522 is online", qos=1, retain=True)
                card = " ".join(["{:02x}".format(x) for x in uid])
                print("Card read UID: %s " % card)
                client.publish(EVENT_TOPIC, '{"card":%s}' % card )
        except KeyboardInterrupt:
            print("End")
            continue_reading = False
        finally:
            client.publish(STATUS_TOPIC, "rc522 dead", qos=1, retain=True)
            client.disconnect()
            GPIO.cleanup()


if __name__ == "__main__":
    main()
