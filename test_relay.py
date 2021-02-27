# External module imports
import RPi.GPIO as GPIO
import time

# Pin Definitons:
relayPin = 26 # Broadcom pin 18 (P1 pin 12)


# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(relayPin, GPIO.OUT) # LED pin set as output

# Initial state for LEDs:
GPIO.output(relayPin, GPIO.LOW)

print("Here we go! Press CTRL+C to exit")
try:
    while 1:
            GPIO.output(relayPin, GPIO.HIGH)
            time.sleep(2)
            GPIO.output(relayPin, GPIO.LOW)
            time.sleep(2)
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup() # cleanup all GPIO

