import os
import sys
import logging
import json
import time
import traceback
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
logging_level = str(os.getenv('LOGGING_LEVEL'))
host = str(os.getenv('BROKER_HOST'))  # MQTT broker hostname/IP address
port = int(os.getenv('BROKER_PORT'))  # MQTT broker network port
client_id = str(os.getenv('CLIENT_ID'))  # MQTT client ID
clean_session = bool(os.getenv('CLEAN_SESSION'))  # True/false (control whether MQTT broker queues messages)
username = str(os.getenv('USERNAME'))  # MQTT broker username/password authentication
password = str(os.getenv('PASSWORD'))  # MQTT broker username/password authentication
avgs_topic = str(os.getenv('AVG_TOPIC'))  # RNG averages MQTT broker topic
refresh_interval = int(os.getenv('REFRESH_INTERVAL'))  # How often (seconds) results table is refreshed
log_format = "%(levelname)s %(asctime)s - %(message)s"
logging_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}
if logging_level not in logging_levels.keys():
    raise Exception("Invalid logging level received: '{0}'. Please provide one of the following as logging level: "
                    "debug, info, warning, error, critical.".format(str(logging_level)))
logging.basicConfig(stream=sys.stdout,
                    format=log_format,
                    level=logging_levels[logging_level])
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
    logging.info("Attempting connection to MQTT broker '{0}'...".format(host))
    # Connect to the MQTT broker
    c.connect(
        host=host,
        port=port)
    logging.info("Successfully connected to MQTT broker '{0}'.".format(host))
    c.subscribe(avgs_topic)  # Subscribe to RNG averages topic
    logging.info("Starting MQTT client network loop...")
    c.loop_start()  # Start the Client network loop, listening for and receiving RNG average updates in another thread.
    logging.info("Successfully started MQTT client network loop.")
    time.sleep(3)  # Give some time for logs to be read and MQTT message to be buffered in the background.
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
    logging.error(traceback.format_exc())
finally:
    logging.info("Stopping MQTT client network loop...")
    c.loop_stop()  # Stop the Client network loop.
    logging.info("Successfully stopped MQTT client network loop.")
    logging.info("Disconnecting from MQTT broker '{0}'...".format(host))
    c.disconnect()  # Disconnect from the MQTT broker.
    logging.info("Successfully disconnected from MQTT broker '{0}'.".format(host))
