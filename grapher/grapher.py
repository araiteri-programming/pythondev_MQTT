import os
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
    print("Attempting connection to MQTT broker '{0}'...".format(host))
    c.connect(
        host=host,
        port=port)
    c.subscribe(rng_topic)  # Subscribe to RNG value MQTT stream from broker.
    c.loop_start()  # Start the client network loop to receive RNG values in the background.
    print("Successfully connected to MQTT broker '{0}'. Starting publish...".format(host))
    print("Starting loop...")
    while True:
        print("Pre-trim datapoint contents: {0}".format(str(data)))
        # Calculate timestamp used to purge old data and calculate 1, 5 and 30 minute RNG value averages from
        # datapoints.
        curr_tstamp = datetime.timestamp(datetime.now())
        data = purge_old_data(data, (curr_tstamp - max_datapoint_age))  # Remove datapoints older than maximum age.
        print("Post-trim datapoint contents: {0}".format(str(data)))
        calc_avgs = {}  # Initialise payload to be published to MQTT broker
        for k in averages_to_calc.keys():
            end_timestamp = curr_tstamp  # Average values are calculated from current time, looking backwards over
            # the dataset.
            start_timestamp = curr_tstamp - averages_to_calc[k]  # Key value specifies max age (in seconds) of
            # datapoints for this average value. E.g. max age of one minute average is 60 seconds.
            calc_avgs[k] = calculate_time_period_average(data, start_timestamp, end_timestamp)
        print('Average values calculated: 1min=={0}, 5min=={1}, 30min=={2}'.format(calc_avgs['one_min_avg'],
                                                                                   calc_avgs['five_min_avg'],
                                                                                   calc_avgs['thirty_min_avg']))
        c.publish(
            topic=avgs_topic,
            payload=json.dumps(calc_avgs)
        )
        print("Successfully published average values to MQTT broker '{0}', topic '{1}'.".format(host, avgs_topic))
        print("Waiting {0} seconds before sending updated MQTT...".format(str(msg_interval)))
        time.sleep(msg_interval)  # Wait the configured wait time before sending another MQTT message.
except Exception as e:
    traceback.print_exc()
finally:
    print("Stopping loop...")
    c.loop_stop()
    print("Disconnecting from MQTT broker '{0}'...".format(host))
    c.disconnect()
    print("Successfully disconnected.")
