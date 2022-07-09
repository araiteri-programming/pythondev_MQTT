import os
import json
import time
import paho.mqtt.client as mqtt
from tabulate import tabulate


def populate_avg_data(client, userdata, message):
    global data
    global counter
    d = json.loads(message.payload)
    d = [[str(d["one_min_avg"]), str(d["five_min_avg"]), str(d["thirty_min_avg"])]]
    data = d
    counter = 0


# Get script vars from env
host = str(os.getenv('BROKER_HOST'))
port = int(os.getenv('BROKER_PORT'))
client_id = str(os.getenv('CLIENT_ID'))
clean_session = bool(os.getenv('CLEAN_SESSION'))
username = str(os.getenv('USERNAME'))
password = str(os.getenv('PASSWORD'))
avgs_topic = str(os.getenv('AVG_TOPIC'))
refresh_interval = int(os.getenv('REFRESH_INTERVAL'))
data = []
counter = 0
headers = ["1min Average", "5min Average", "30min Average"]
c = mqtt.Client(
    client_id=client_id,
    clean_session=clean_session)
c.message_callback_add(avgs_topic, populate_avg_data)
c.username_pw_set(
    username=username,
    password=password)
try:
    print("Attempting connection to MQTT broker '{0}'...".format(host))
    c.connect(
        host=host,
        port=port)
    c.subscribe(avgs_topic)
    c.loop_start()
    print("Successfully connected to MQTT broker '{0}'.".format(host))
    print("Starting loop...")
    while True:
        os.system('clear')  # Clear the screen of all other output.
        print("Seconds since last MQTT update: {0}".format(str(counter)))  # Print time since last MQTT message received.
        if len(data) == 1:  # There is MQTT data to print.
            print(tabulate(
                data,
                headers=headers,
                tablefmt="grid"))
        else:  # No MQTT data received yet.
            print("Awaiting MQTT data to tabulate...")
        counter += 1
        time.sleep(refresh_interval)  # Wait the configured wait time before doing a console update.
except Exception as e:
    print(str(e))
finally:
    print("Stopping loop...")
    c.loop_stop()
    print("Disconnecting from MQTT broker '{0}'...".format(host))
    c.disconnect()
    print("Successfully disconnected.")
