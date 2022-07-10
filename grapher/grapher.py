import os
import json
import time
import datetime
import paho.mqtt.client as mqtt


# Function is used for MQTT callback, receiving RNG datapoints and adding it to the data list.
def add_rng_datapoint(client, userdata, message):
    global data
    datapoint = json.loads(message.payload)
    data.append(datapoint)


# Function purges all datapoints that are 30+ minutes older than the timestamp passed to the function.
def purge_old_data(timestamp):
    global data
    new_data = []
    # Populate a working list of all data that isn't older than 30 minutes.
    for d in data:
        if d["timestamp"] + 1800 >= timestamp:
            new_data.append(d)
    data = new_data  # Overwrite existing data set with new data set with expired datapoints omitted.


# Function iterates through all stored data, calculating 1+5+30 minute averages over all the data and returns those
# values.
def calculate_avgs(timestamp):
    global data
    avgs = {}
    datapoints = 0
    total = 0
    # Find all entries <= 1 minute old and add to working sum.
    for d in data:
        if d["timestamp"] + 60 >= timestamp:
            datapoints += 1
            total = total + int(d["rng_value"])
    # Calculate 1 minute average, or return 0 to indicate no datapoints in 1 minute period.
    if total != 0:
        avgs["one_min_avg"] = total / datapoints
    else:
        avgs["one_min_avg"] = 0
    datapoints = 0
    total = 0
    # Find all entries <= 5 minutes old and add to working sum.
    for d in data:
        if d["timestamp"] + 300 >= timestamp:
            datapoints += 1
            total = total + int(d["rng_value"])
    # Calculate 5 minute average, or return 0 to indicate no datapoints in 5 minute period.
    if total != 0:
        avgs["five_min_avg"] = total / datapoints
    else:
        avgs["five_min_avg"] = 0
    datapoints = 0
    total = 0
    # Find all entries <= 30 minutes old and add to working sum.
    for d in data:
        if d["timestamp"] + 1800 >= timestamp:
            datapoints += 1
            total = total + int(d["rng_value"])
    # Calculate 30 minute average, or return 0 to indicate no datapoints in 30 minute period.
    if total != 0:
        avgs["thirty_min_avg"] = total / datapoints
    else:
        avgs["thirty_min_avg"] = 0
    return avgs


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
data = []
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
        curr_date = datetime.datetime.now()
        curr_tstamp = datetime.datetime.timestamp(curr_date)
        purge_old_data(curr_tstamp)  # Remove datapoints too old for 1, 5 and 30 minute averages.
        print("Post-trim datapoint contents: {0}".format(str(data)))
        calc_avgs = calculate_avgs(curr_tstamp)
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
    print(str(e))
finally:
    print("Stopping loop...")
    c.loop_stop()
    print("Disconnecting from MQTT broker '{0}'...".format(host))
    c.disconnect()
    print("Successfully disconnected.")
