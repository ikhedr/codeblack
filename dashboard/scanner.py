import requests
import json
from time import sleep  # Import the sleep function from the time module

platform = "windows"
if not platform == 'windows':
    import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library

    GPIO.setwarnings(False)  # Ignore warning for now
    GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
    GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW)  # Set pin 8 to be an output pin and set initial value to low (off)
    GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)

bin = None
product = None
transfer_order = None
headers = {'content-type': 'application/json'}

while True:
    print("Waiting for input:")
    barcode_scaned_data = input()

    if barcode_scaned_data.startswith('TO', 0, 2):
        transfer_order = barcode_scaned_data
        try:
            to_response = requests.post("http://127.0.0.1:5000/check_transfer_order",
                                        data=json.dumps({"to_number": transfer_order[2:]}), headers=headers)
            to_response = json.loads(to_response.text)
        except:
            print("Exception")
            to_response = 'failure'
        if to_response == "failure":
            if not platform == 'windows':
                GPIO.output(11, GPIO.HIGH)  # Turn on
                sleep(1)
                GPIO.output(11, GPIO.LOW)
            print(to_response)
            transfer_order = None
            continue
    elif barcode_scaned_data.startswith('B', 0, 1):
        bin = barcode_scaned_data
    else:
        product = barcode_scaned_data
    if transfer_order:
        if bin and product:
            bin_id, product_id = tuple(bin.split("-"))
            bin_id = bin_id[1:]

            if not product == product_id:
                if not platform == 'windows':
                    GPIO.output(11, GPIO.HIGH)  # Turn on
                    sleep(2)
                    GPIO.output(11, GPIO.LOW)
            else:
                # Update scanned status to Database
                try:
                    response = requests.post("http://127.0.0.1:5000/update_product_details",
                                             data=json.dumps({"to_number": transfer_order[2:], "dest__bin": bin_id,
                                                              "material": product}), headers=headers)
                    response = json.loads(response.text)
                except:
                    print("Exception")
                    response = 'failure'
                if response == "success":
                    if not platform == 'windows':
                        GPIO.output(7, GPIO.HIGH)  # Turn on
                        sleep(3)
                        GPIO.output(7, GPIO.LOW)
                elif response == "failure":
                    if not platform == 'windows':
                        GPIO.output(11, GPIO.HIGH)  # Turn on
                        sleep(3)
                        GPIO.output(11, GPIO.LOW)
                print(response)
            bin = None
            product = None
