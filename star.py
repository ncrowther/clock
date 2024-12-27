from machine import Pin, PWM
from time import sleep

# Initialize PWM for each color channel of an RGB LED
red = PWM(Pin(2))  # Red channel on GPIO pin 26
green = PWM(Pin(3))  # Green channel on GPIO pin 27
blue = PWM(Pin(4))  # Blue channel on GPIO pin 28

# Set 1000 Hz frequency for all channels
red.freq(1000)
green.freq(1000)
blue.freq(1000)


# Function to set RGB LED color
def set_color(r, g, b):
    red.duty_u16(r)  # Red intensity
    green.duty_u16(g)  # Green intensity
    blue.duty_u16(b)  # Blue intensity


try:
    while True:
        set_color(65535, 0, 0)  # Red
        sleep(0.33)
        set_color(0, 65535, 0)  # Green
        sleep(0.33)
        set_color(0, 0, 65535)  # Blue
        sleep(0.33)
        set_color(65535, 65535, 40535)  # White   
        sleep(59)
        
except KeyboardInterrupt:
    set_color(0, 0, 0)  # Turn off RGB LED on interrupt
