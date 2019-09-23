import requests
import json
import time
import paho.mqtt.client as mqtt
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
broker = s.getsockname()[0]
s.close()

columns = ['station_id', 'bin_id', 'status']
col_len = len(columns)
headers = {'content-type': 'application/json'}


def on_message(client, userdata, message):
    time.sleep(1)
    instance_data = {}
    if message:
        message = str(message.payload.decode("utf-8")).split(";")
        # Check number of columns received is same as defined
        print(message)
        if len(message) == 3:
            for i in range(0, len(columns)):
                instance_data[columns[i]] = message[i]
                i = i + 1
        else:
            print("data missing from the payload. Checkout the sensor output.")
            return 1
    else:
        print("Didn't recieve message. Checkout the sensor output.")
        return 1
    try:
        api_response = requests.post("http://127.0.0.1:5000/update_bin_status",
                                     data=json.dumps(instance_data), headers=headers)
    except:
        print("Exception")
        api_response = json.dumps("failure")
    api_response = json.loads(api_response.text)
    print(api_response)
    if api_response == "success":
        print(type(instance_data))
        print("Success: received message = {0}".format(instance_data))
    elif api_response == "failure":
        print("API failure: Something went wrong")


clients = []
nclients = 1
mqtt.Client.connected_flag = False
# create clients
for i in range(nclients):
    cname = "Client" + str(i)
    client = mqtt.Client(cname)
    clients.append(client)
print("connecting to broker ", broker)
for client in clients:
    client.on_message = on_message
    client.connect(broker, 1883)
    client.loop_start()
    client.subscribe("bin_status")
print("Started listening...")
while True:
    pass

for client in clients:
    client.disconnect()
    client.loop_stop()
# client = mqtt.Client("client-001")  # create client object client1.on_publish = on_publish #assign function to callback client1.connect(broker,port) #establish connection client1.publish("house/bulb1","on")
# client1 = mqtt.Client("client-002")

######Bind function to callback
# client.on_message = on_message
# client1.on_message = on_message
#####
# print("connecting to broker ", broker)
'''client.connect(broker, 1883)  # connect
client1.connect(broker, 1883)
client.loop_start()  # start loop to process received messages
client1.loop_start()
print("subscribing ")
client.subscribe("binstatus")  # subscribe
client1.subscribe("binstatus") 
while True:
    pass
client.disconnect()  # disconnect
client1.disconnect() 
client.loop_stop()  # loop_forever()
client1.loop_stop()'''
