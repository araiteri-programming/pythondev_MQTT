import os
import sys
import logging
import json
import time
import traceback
from datetime import datetime
import paho.mqtt.client as mqtt


# Function is used for MQTT callback, receiving RNG datapoints and adding it to the data list.
def add_rng_datapoint(client, userdata, message):
    global data
    datapoint = json.loads(message.payload)
    data.append(datapoint)


# Function purges all datapoints that are older than the minimum timestamp.
def purge_old_data(data, minimum_timestamp):
    working_list = []
    for d in data:
        if d["timestamp"] >= minimum_timestamp:
            working_list.append(d)
    return working_list


# Function calculates the average RNG value over datapoints that fall within the start and end timestamps.
def calculate_time_period_average(data, start_timestamp, end_timestamp):
    working_list = []
    for d in data:
        if start_timestamp <= d['timestamp'] <= end_timestamp:
            working_list.append(int(d['rng_value']))
    if len(working_list) > 0:
        return sum(working_list) / len(working_list)
    else:
        return 0


# Get script vars from env
logging_level = str(os.getenv('LOGGING_LEVEL'))
host = str(os.getenv('BROKER_HOST'))
port = int(os.getenv('BROKER_PORT'))
client_id = str(os.getenv('CLIENT_ID'))
clean_session = bool(os.getenv('CLEAN_SESSION'))  # True/false (control whether MQTT broker queues messages)
username = str(os.getenv('USERNAME'))  # MQTT username/password authentication
password = str(os.getenv('PASSWORD'))  # MQTT username/password authentication
rng_topic = str(os.getenv('RNG_TOPIC'))  # Topic on which RNG values will be received.
avgs_topic = str(os.getenv('AVG_TOPIC'))  # Topic to publish calculated averages on.
msg_interval = int(os.getenv('MSG_INTERVAL'))  # How often calculated averages should be published.
max_datapoint_age = int(os.getenv('MAX_DATAPOINT_AGE'))  # Maximum age of received datapoints before they are purged.
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
data = []  # Initialise RNG value dataset
# Each key-value pair defined here is an average value that will be calculated and published to the MQTT broker.
averages_to_calc = {
    'one_min_avg': 60,
    'five_min_avg': 300,
    'thirty_min_avg': 1800
}
c = mqtt.Client(
    client_id=client_id,
    clean_session=clean_session)
c.message_callback_add(rng_topic, add_rng_datapoint)  # Add callback that will receive RNG values in the background
# thread, while the main thread publishes calculated average values back to the broker.
c.username_pw_set(
    username=username,
    password=password)
try:
    logging.info("Attempting connection to MQTT broker '{0}'...".format(host))
    c.connect(
        host=host,
        port=port)
    logging.info("Successfully connected to MQTT broker '{0}'.".format(host))
    c.subscribe(rng_topic)  # Subscribe to RNG value MQTT stream from broker.
    logging.info("Starting MQTT client network loop...")
    c.loop_start()  # Start the client network loop to receive RNG values in the background.
    logging.info("Successfully started MQTT client network loop.")
    print("Starting publish stream of RNG average values...")
    while True:
        logging.debug("Pre-purge dataset contents: {0}".format(str(data)))
        # Calculate timestamp used to purge old data and calculate 1, 5 and 30 minute RNG value averages from
        # datapoints.
        curr_tstamp = datetime.timestamp(datetime.now())
        data = purge_old_data(data, (curr_tstamp - max_datapoint_age))  # Remove datapoints older than maximum age.
        logging.debug("Post-purge dataset contents: {0}".format(str(data)))
        calc_avgs = {}  # Initialise payload to be published to MQTT broker
        for k in averages_to_calc.keys():
            end_timestamp = curr_tstamp  # Average values are calculated from current time, looking backwards over
            # the dataset.
            start_timestamp = curr_tstamp - averages_to_calc[k]  # Key value specifies max age (in seconds) of
            # datapoints for this average value. E.g. max age of one minute average is 60 seconds.
            calc_avgs[k] = calculate_time_period_average(data, start_timestamp, end_timestamp)
        c.publish(
            topic=avgs_topic,
            payload=json.dumps(calc_avgs)
        )
        log_str = "Successfully published RNG average values to MQTT broker '{0}', topic '{1}'. " \
                  "Average values:\n".format(host, rng_topic)
        for k in calc_avgs.keys():
            log_str = log_str + "{0}: {1}\n".format(k, str(calc_avgs[k]))
        logging.info(log_str)
        logging.info("Waiting {0} seconds before sending updated MQTT...".format(str(msg_interval)))
        time.sleep(msg_interval)  # Wait the configured wait time before sending another MQTT message.
except Exception as e:
    logging.error(traceback.format_exc())
finally:
    print("RNG average value publishing stopped.")
    logging.info("Stopping MQTT client network loop...")
    c.loop_stop()  # Stop the Client network loop.
    logging.info("Successfully stopped MQTT client network loop.")
    logging.info("Disconnecting from MQTT broker '{0}'...".format(host))
    c.disconnect()  # Disconnect from the MQTT broker.
    logging.info("Successfully disconnected from MQTT broker '{0}'.".format(host))
