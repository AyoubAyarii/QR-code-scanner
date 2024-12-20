import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
import urllib.request
import serial
import webbrowser
import requests  # To send data to Firebase
import time  # For timestamp generation

# Firebase settings
firebase_url = ""  # Replace with your database URL
firebase_auth_key = ""  # Replace with your Firebase auth key (if needed)
# Serial port settings
serial_port = 'COM7'  # Replace with your ESP32 serial port
baud_rate = 115200

# Initialize serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Camera URL
url = 'http://192.168.1.152'
cv2.namedWindow("live transmission", cv2.WINDOW_AUTOSIZE)

prev = ""  # To avoid duplicate processing
pres = ""

def send_to_firebase(data):
    """Send QR code data with a timestamp to Firebase Realtime Database."""
    timestamp = int(time.time() * 1000)  # Current time in milliseconds
    payload = {
        "qr_data": data,
        "time_logged": timestamp
    }
    response = requests.post(firebase_url + "qr_codes.json", json=payload)
    if response.status_code == 200:
        print("Data sent to Firebase successfully.")
    else:
        print("Failed to send data to Firebase:", response.text)

while True:
    try:
        # Fetch the camera image
        img_resp = urllib.request.urlopen(url + 'cam-hi.jpg')
        imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        frame = cv2.imdecode(imgnp, -1)

        # Decode QR codes in the frame
        decodedObjects = pyzbar.decode(frame)
        for obj in decodedObjects:
            pres = obj.data.decode('utf-8')  # Decode bytes to string
            if prev != pres:
                print("Type:", obj.type)
                print("Data:", pres)
                prev = pres

                # Send QR code data to ESP32 via serial
                ser.write((pres + "\n").encode('utf-8'))
                
                # Display data on the frame
                cv2.putText(frame, pres, (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 3)

                # Send data to Firebase
                send_to_firebase(pres)

                # Check if the data is a URL and open it in a browser
                if pres.startswith("http://") or pres.startswith("https://"):
                    print("Opening URL:", pres)
                    webbrowser.open(pres)
                else:
                    print("QR Code Data:", pres)

        # Display the live video transmission
        cv2.imshow("live transmission", frame)

        # Exit loop on ESC key
        key = cv2.waitKey(1)
        if key == 27:
            break

    except Exception as e:
        print("Error:", e)
        break

# Cleanup
ser.close()
cv2.destroyAllWindows()
