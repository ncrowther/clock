from machine import Pin, PWM
from time import sleep

##############################
"""
LightStar - interface to RGB LED

Methods:
    illuminate
"""
class LightStar(object):

    def __init__(self): 
        # Initialize PWM for each color channel of an RGB LED
        self.red = PWM(Pin(2))  # Red channel on GPIO pin 26
        self.green = PWM(Pin(6))  # Green channel on GPIO pin 27
        self.blue = PWM(Pin(7))  # Blue channel on GPIO pin 28

        # Set 1000 Hz frequency for all channels
        self.red.freq(1000)
        self.green.freq(1000)
        self.blue.freq(1000)
        
        self.MAX_BRIGHTNESS = 65535
        self.MIN_BRIGHTNESS = 5535

    # Function to set RGB LED color
    def light(self, r, g, b):
        self.red.duty_u16(r)  # Red intensity
        self.green.duty_u16(g)  # Green intensity
        self.blue.duty_u16(b)  # Blue intensity

    # Method to set RGB LED color
    def off(self):
        self.light(0, 0, 0)  # White
        
    # Method to set RGB LED color
    def illuminate(self, hour):
                  
        MULTIPLIER = 3600
        greenBrightness = 32000
        
        redBrightness = (hour * MULTIPLIER) +  20000
        
        hour  = abs(hour - 23)
        blueBrightness = abs((hour * MULTIPLIER) - 10000)
        
        if (redBrightness >= self.MAX_BRIGHTNESS):
            redBrightness = self.MAX_BRIGHTNESS
            
        if (blueBrightness >= self.MAX_BRIGHTNESS):
            blueBrightness = 0           
          
        print("Red Brightness: " + str(redBrightness))
        print("Blue Brightness: " + str(blueBrightness))
        
        self.light(redBrightness, greenBrightness, blueBrightness)  


def main():
    
    lightStar = LightStar()
    hour = 0
    
    while True:
        lightStar.illuminate(hour)
        hour = hour + 1
        
        print(hour)
        if (hour == 23):
           hour = 0
           
        sleep(0.5)
    
    
    
if __name__ == "__main__":
    main()     