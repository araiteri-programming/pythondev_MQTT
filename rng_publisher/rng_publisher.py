import os
import random
import time
import paho.mqtt.client as mqtt


# Get script vars from env
host = str(os.getenv('BROKER_HOST'))
port = int(os.getenv('BROKER_PORT'))
client_id = str(os.getenv('CLIENT_ID'))
clean_session = bool(os.getenv('CLEAN_SESSION'))
username = str(os.getenv('USERNAME'))
password = str(os.getenv('PASSWORD'))
topic = str(os.getenv('TOPIC'))
while True:
    c = mqtt.Client(
        client_id=client_id,
        clean_session=clean_session)
    try:
        print("Connecting to MQTT broker '{0}' with client ID '{1}'...".format(host, client_id))
        print("Initiating a clean session: {0}".format(str(clean_session)))
        c.username_pw_set(
            username=username,
            password=password
        )
        print("Username '{0}' and password '{1}' set.".format(username, password))
        c.username_pw_set(
            username=username,
            password=password)
        c.connect(
            host=host,
            port=port)
        print("Successfully connected.")
        print("Starting publish stream of RNG values...")
        while True:
            try:
                rng_value = str(random.choice(range(1, 100)))
                print("RNG value to publish to broker is {0}.".format(rng_value))
                c.publish(
                    topic=topic,
                    payload=rng_value)
                print("Successfully published RNG value {0} to MQTT broker '{1}', topic '{2}'.".format(rng_value, host, topic))
                interval = random.choice(range(1, 30))
                print("Sleeping for {0} seconds before publishing again...".format(str(interval)))
                time.sleep(interval)
            except Exception as e:
                print(str(e))
    except Exception as e:
        print(str(e))
    finally:
        print("Disconnecting from MQTT broker '{0}'...".format(host))
        c.disconnect()
        print("Successfully disconnected.")
