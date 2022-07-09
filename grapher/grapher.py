import os
import json
import time
import datetime
import paho.mqtt.client as mqtt


def add_rng_datapoint(client, userdata, message):
    global data
    datapoint = json.loads(message.payload)
    data.append(datapoint)


def purge_old_data(timestamp):
    global data
    new_data = []  # Initialise new datapoint list.
    for d in data:
        if d["timestamp"] + 1800 >= timestamp:  # If data is less than 30 minutes old,
            new_data.append(d)  # Add fresh data to working list.
    data = new_data  # Overwrite global datapoint list with trimmed list.


def calculate_avgs(timestamp):
    global data
    avgs = {}
    datapoints = 0
    total = 0
    for d in data:
        if d["timestamp"] + 60 >= timestamp:  # If data is less than or equal to one minute old,
            datapoints += 1
            total = total + int(d["rng_value"])
    if total != 0:
        avgs["one_min_avg"] = total / datapoints
    else:
        avgs["one_min_avg"] = 0
    datapoints = 0
    total = 0
    for d in data:
        if d["timestamp"] + 300 >= timestamp:  # If data is less than or equal to five minutes old,
            datapoints += 1
            total = total + int(d["rng_value"])
    if total != 0:
        avgs["five_min_avg"] = total / datapoints
    else:
        avgs["five_min_avg"] = 0
    datapoints = 0
    total = 0
    for d in data:
        if d["timestamp"] + 1800 >= timestamp:  # If data is less than or equal to 30 minutes old,
            datapoints += 1
            total = total + int(d["rng_value"])
    if total != 0:
        avgs["thirty_min_avg"] = total / datapoints
    else:
        avgs["thirty_min_avg"] = 0
    return avgs


# Get script vars from env
host = str(os.getenv('BROKER_HOST'))
port = int(os.getenv('BROKER_PORT'))
client_id = str(os.getenv('CLIENT_ID'))
clean_session = bool(os.getenv('CLEAN_SESSION'))
username = str(os.getenv('USERNAME'))
password = str(os.getenv('PASSWORD'))
rng_topic = str(os.getenv('RNG_TOPIC'))
avgs_topic = str(os.getenv('AVG_TOPIC'))
msg_interval = int(os.getenv('MSG_INTERVAL'))
data = []
c = mqtt.Client(
    client_id=client_id,
    clean_session=clean_session)
c.message_callback_add(rng_topic, add_rng_datapoint)
c.username_pw_set(
    username=username,
    password=password)
try:
    print("Attempting connection to MQTT broker '{0}'...".format(host))
    c.connect(
        host=host,
        port=port)
    c.subscribe(rng_topic)
    c.loop_start()
    print("Successfully connected to MQTT broker '{0}'. Starting publish...".format(host))
    print("Starting loop...")
    while True:
        print("Pre-trim datapoint contents: {0}".format(str(data)))
        curr_date = datetime.datetime.now()
        curr_tstamp = datetime.datetime.timestamp(curr_date)
        purge_old_data(curr_tstamp)
        print("Post-trim datapoint contents: {0}".format(str(data)))
        calc_avgs = calculate_avgs(curr_tstamp)
        print('Average values calculated: 1min=={0}, 5min=={1}, 30min=={2}'.format(calc_avgs['one_min_avg'], calc_avgs['five_min_avg'], calc_avgs['thirty_min_avg']))
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
