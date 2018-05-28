import machine
import ubinascii as binascii

from umqtt.simple import MQTTClient

from config import broker, mqtt_password, mqtt_user

machine_id = binascii.hexlify(machine.unique_id())
print(b"Machine ID: {}".format(machine_id))

client = None


class RelayPin(object):
    def __init__(self, value):
        self.v = value

    def value(self):
        return self.v


relay_pin = RelayPin('on')


def callback(topic, msg):
    if topic == topic_name(b"control"):
        try:
            msg_type, payload = msg.split(b":", 1)
            if msg_type == b"h":
                print(payload)
            else:
                print("Unknown message type, ignoring")
        except Exception:
            print("Couldn't parse/handle message, ignoring.")
    elif topic == topic_name(b"config"):
        load_config(msg)


def publish_state():
    if relay_pin.value():
        client.publish(topic_name(b"state"), b"on")
    else:
        client.publish(topic_name(b"state"), b"off")
    print("Relay state: {}".format("on" if relay_pin.value() else "off"))


def topic_name(topic):
    return b"/".join([b"light", machine_id, topic])


def connect_and_subscribe():
    global client
    client = MQTTClient(machine_id, broker,
                        user=mqtt_user,
                        password=mqtt_password)
    client.set_last_will(topic_name(b'lwt'), 'our lwt')
    client.set_callback(callback)
    client.connect()
    print("Connected to {}".format(broker))
    for topic in (b'config', b'control'):
        t = topic_name(topic)
        client.subscribe(t)
        print("Subscribed to {}".format(t))

    publish_state()


def load_config(msg):
    import ujson as json
    try:
        config = json.loads(msg)
    except (OSError, ValueError):
        print("Couldn't load config from JSON, bailing out.")
    else:
        pass


def setup():
    connect_and_subscribe()


def main_loop():
    while 1:
        client.wait_msg()


def teardown():
    try:
        client.disconnect()
        print("Disconnected.")
    except Exception:
        print("Couldn't disconnect cleanly.")


if __name__ == '__main__':
    setup()
    try:
        main_loop()
    finally:
        teardown()
