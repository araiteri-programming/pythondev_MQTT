import os
import sys
import logging
import random
import time
import json
import traceback
from datetime import datetime
import paho.mqtt.client as mqtt


# Get script vars from env
logging_level = str(os.getenv('LOGGING_LEVEL'))
host = str(os.getenv('BROKER_HOST'))
port = int(os.getenv('BROKER_PORT'))
client_id = str(os.getenv('CLIENT_ID'))
clean_session = bool(os.getenv('CLEAN_SESSION'))  # True/false (control whether MQTT broker queues messages)
username = str(os.getenv('USERNAME'))  # MQTT username/password authentication
password = str(os.getenv('PASSWORD'))  # MQTT username/password authentication
rng_topic = str(os.getenv('RNG_TOPIC'))  # Topic to publish RNG values on.
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
while True:
    c = mqtt.Client(
        client_id=client_id,
        clean_session=clean_session)
    try:
        c.username_pw_set(
            username=username,
            password=password)
        logging.info("Attempting connection to MQTT broker '{0}'...".format(host))
        c.connect(
            host=host,
            port=port)
        logging.info("Successfully connected to MQTT broker '{0}'.".format(host))
        print("Starting publish stream of RNG values...")
        while True:
            try:
                curr_tstamp = datetime.timestamp(datetime.now())
                rng_value = str(random.choice(range(1, 100)))
                logging.info("RNG value to publish to broker is {0}.".format(rng_value))
                payload = {'timestamp': curr_tstamp, 'rng_value': rng_value}
                c.publish(
                    topic=rng_topic,
                    payload=json.dumps(payload))
                logging.info("Successfully published RNG value {0} to MQTT broker '{1}', "
                             "topic '{2}'.".format(rng_value, host, rng_topic))
                time_till_next_message = random.choice(range(1, 30))
                logging.info("Sleeping for {0} seconds before publishing again...".format(str(time_till_next_message)))
                time.sleep(time_till_next_message)
            except Exception as e:
                logging.error(traceback.format_exc())
    except Exception as e:
        logging.error(traceback.format_exc())
    finally:
        print("RNG value publishing stopped.")
        logging.info("Disconnecting from MQTT broker '{0}'...".format(host))
        c.disconnect()
        logging.info("Successfully disconnected from MQTT broker '{0}'.".format(host))
