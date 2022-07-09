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
host = str(os.getenv('BROKER_HOST'))  # MQTT broker hostname/IP address
port = int(os.getenv('BROKER_PORT'))  # MQTT broker network port
client_id = str(os.getenv('CLIENT_ID'))  # MQTT client ID
clean_session = bool(os.getenv('CLEAN_SESSION'))  # True/false (control whether MQTT broker queues messages)
username = str(os.getenv('USERNAME'))  # MQTT broker username/password authentication
password = str(os.getenv('PASSWORD'))  # MQTT broker username/password authentication
avgs_topic = str(os.getenv('AVG_TOPIC'))  # RNG averages MQTT broker topic
refresh_interval = int(os.getenv('REFRESH_INTERVAL'))  # How often (seconds) results table is refreshed
data = []  # List that holds all MQTT data subscribed to by this node.
counter = 0  # Counter that tracks time since last MQTT message
headers = ["1min Average", "5min Average", "30min Average"]  # Table headers
# Declare paho-mqtt Client object
c = mqtt.Client(
    client_id=client_id,
    clean_session=clean_session)
c.message_callback_add(avgs_topic, populate_avg_data)  # Add custom callback for RNG averages subscription
# Set MQTT broker authentication
c.username_pw_set(
    username=username,
    password=password)
try:
    print("Attempting connection to MQTT broker '{0}'...".format(host))
    # Connect to the MQTT broker
    c.connect(
        host=host,
        port=port)
    print("Successfully connected to MQTT broker '{0}'.".format(host))
    c.subscribe(avgs_topic)  # Subscribe to RNG averages topic
    c.loop_start()  # Start the Client network loop, listening for and receiving RNG average updates in another thread.
    print("Starting loop...")
    while True:
        os.system('clear')  # Clear the screen of all other output.
        print("Seconds since last MQTT update: {0}".format(str(counter)))  # Print time since last MQTT message
        # received.
        if len(data) == 1:  # There is MQTT data to print. Print the data in table format.
            print(tabulate(
                data,
                headers=headers,
                tablefmt="grid"))
        else:  # No MQTT data received yet.
            print("Awaiting MQTT data to tabulate...")
        counter += 1  # Increment 'time since MQTT message' counter.
        time.sleep(refresh_interval)  # Wait the configured wait time before refreshing the screen.
except Exception as e:
    print(str(e))
finally:
    print("Stopping loop...")
    c.loop_stop()  # Stop the Client network loop.
    print("Disconnecting from MQTT broker '{0}'...".format(host))
    c.disconnect()  # Disconnect from the MQTT broker.
    print("Successfully disconnected.")
