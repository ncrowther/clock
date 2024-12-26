from machine import Pin, I2C
import ssd1306
import ds1302
import time
import array
import rp2
import math
import dht
import random


"""
Clock
======

Author: Nigel T. Crowther
Date:   16th December 2024

Clock code to control:
 -  A NeoPixel ring representing seconds,
 -  An OLED display to show date, time, temperature and humitity
 - A servo motor to chime hourly.

The code continuously displays the current datetime on the OLED display, and updates the NeoPixel ring to show the seconds.
If it is between 9am and 9pm, the servo motor will chime the hour.

The code also allows the user to adjust the volume of the chime using a volume button.
The user can also adjust the hour, minute, and second using separate buttons.

The code uses the following libraries:
- machine: for hardware access
- ssd1306: for OLED display
- ds1302: for RTC
- time: for time-related functions
- rp2: for Rasbperry Pi Pico hardware access
- math: for mathematical operations

The code is written in Python and is designed to run on a Raspberry Pi Pico board.
"""

    
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

########################################################################## 
class PhotoResistor(object):

    ADC_PIN = 26
    DARK_THRESHOLD = 50000
    
    def __init__(self):   
        # Initialize DHT11 sensor on GPIO
        self.photoresistor = machine.ADC(self.ADC_PIN)  # Initialize ADC on pin 26

    def isDark(self):
        lightLevel = self.photoresistor.read_u16()  # Read analog value
        #print("Light level: " + str(lightLevel))  # Print the value
        
        if (lightLevel > self.DARK_THRESHOLD):
            #print("Light ON")
            return True
        else:
            #print("LIGHT OFF")
            return False


########################################################################## 
class TemperatureHumiditySensor(object):
    
    GPIO_PIN = 28
    
    def __init__(self):   
        # Initialize DHT11 sensor on GPIO
        self.sensor = dht.DHT11(machine.Pin(self.GPIO_PIN))

    def read(self):
        self.sensor.measure()
        
        return [self.sensor.temperature(), self.sensor.humidity()]
        #print("Temperature:" ,d.temperature())  # Print temperature
        #print("Humidity:" ,d.humidity())  # Print humidity
        
  
##########################################################################
"""
NeoPixelRing class for controlling NeoPixel rings.

Attributes:
    NUM_LEDS (int): Number of WS2812 LEDs.
    PIN_NUM (int): Pin number for outputting data.
    BRIGHTNESS (float): Brightness level for the LEDs.
    BLACK (tuple): RGB value for black.
    RED (tuple): RGB value for red.
    YELLOW (tuple): RGB value for yellow.
    GREEN (tuple): RGB value for green.
    CYAN (tuple): RGB value for cyan.
    BLUE (tuple): RGB value for blue.
    PURPLE (tuple): RGB value for purple.
    WHITE (tuple): RGB value for white.
    COLORS (tuple): Tuple of RGB values for colors.
    NUMBER_OF_COLORS (int): Number of colors in the COLORS tuple.
    sm (rp2.StateMachine): StateMachine for outputting data.
    ar (array.array): Array of LED RGB values.
    colorIndex (int): Index of the current color in the COLORS tuple.

Methods:
    __init__(self): Initializes the NeoPixelRing object.
    setBrightness(self, level): Sets the brightness level for the LEDs.
    pixels_show(self): Shows the LEDs with the current RGB values.
    pixels_set(self, i, color): Sets the RGB value of a specific LED.
    pixels_fill(self, color): Fills all LEDs with a specific RGB value.
    clockTick(self, color, wait): Performs a clock tick animation.
    color_chase(self, color, wait): Performs a color chase animation.
    tick(self, color, sec): Performs a tick animation based on the time.
    wheel(self, pos): Calculates the RGB value for a specific position.
    rainbow_cycle(self, wait): Performs a rainbow cycle animation.
    getNextColor(self): Gets the next color in the COLORS tuple.
"""
class NeoPixelRing(object):

    # Configure the number of WS2812 LEDs.
    NUM_LEDS = 60 
    PIN_NUM = 0
    BRIGHTNESS = 0.1
    
    # COLORS
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 150, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PURPLE = (180, 0, 255)
    WHITE = (255, 255, 255)
    #COLORS = (WHITE, RED, WHITE, GREEN, WHITE, BLUE, CYAN, PURPLE, WHITE, BLUE)
    COLORS = (WHITE, CYAN, BLUE, PURPLE, RED, GREEN, YELLOW)
    NUMBER_OF_COLORS = len(COLORS)

    def __init__(self): 
    
        # Create the StateMachine with the ws2812 program, outputting on pin
        self.sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(self.PIN_NUM))

        # Start the StateMachine, it will wait for data on its FIFO.
        self.sm.active(1)

        # Display a pattern on the LEDs via an array of LED RGB values.
        self.ar = array.array("I", [0 for _ in range(self.NUM_LEDS)])
        
        self.colorIndex = 0

    """
    Set the brightness of the pixels.

    Args:
        level (int): The brightness level, from 0 to 255.

    Returns:
        None
    """
    def setBrightness(self, level):
        self.BRIGHTNESS = level

    """
    Show the pixels with the current brightness level.

    Returns:
        None
    """
    def pixels_show(self):
        dimmer_ar = array.array("I", [0 for _ in range(self.NUM_LEDS)])
        for i,c in enumerate(self.ar):
            r = int(((c >> 8) & 0xFF) * self.BRIGHTNESS)
            g = int(((c >> 16) & 0xFF) * self.BRIGHTNESS)
            b = int((c & 0xFF) * self.BRIGHTNESS)
            dimmer_ar[i] = (g<<16) + (r<<8) + b
        self.sm.put(dimmer_ar, 8)
        time.sleep_ms(10)

    """
    Set the color of a specific pixel.

    Args:
        i (int): The index of the pixel to set.
        color (tuple): A tuple of three integers representing the RGB color values.

    Returns:
        None
    """
    def pixels_set(self, i, color):
        self.ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]

    """
    Fill all pixels with a specific color.

    Args:
        color (tuple): A tuple of three integers representing the RGB color values.

    Returns:
        None
    """
    def pixels_fill(self, color):
        for i in range(len(self.ar)):
            self.pixels_set(i, color)

    """
    Tick the clock ring by changing the color of each pixel in reverse order.

    Args:
        color (tuple): A tuple of three integers representing the RGB color values.

    Returns:
        None
    """
    def clockTick(self, color):
        for i in range(self.NUM_LEDS)[::-1]:
            self.pixels_set(i, color)
            self.pixels_show()
        
    """
    Chase the color by changing the color of each pixel in reverse order.

    Args:
        color (tuple): A tuple of three integers representing the RGB color values.
        wait (float): The time to wait between each pixel change, in seconds.

    Returns:
        None
    """   
    def color_chase(self, color, wait):
        for i in range(self.NUM_LEDS):
            previousPixel = 59 if (i == 0) else i - 1
            self.pixels_set(previousPixel, self.BLACK)
            self.pixels_set(i, color)
            time.sleep(wait)
            self.pixels_show()
            
    """
    Tick the clock by changing the color of the pixel corresponding to the current second.

    Args:
        color (tuple): A tuple of three integers representing the RGB color values.
        sec (int): The current second.

    Returns:
        None
    """            
    def tick(self, color, sec):
            
        #pixel = ((sec / 60)  * self.NUM_LEDS - 1)
        #previousPixel = 0 if (pixel >= self.NUM_LEDS-3) else pixel + 1
        
        pixel = sec #math.ceil(pixel)
        
        #print(pixel)
        
        #self.pixels_set(previousPixel, self.BLACK)
        self.pixels_set(pixel, color)
        self.pixels_show()
     
    """
    Generate a color value based on the input position.

    Args:
        pos (int): The position value, from 0 to 255.

    Returns:
        tuple: A tuple of three integers representing the RGB color values.
    """     
    def wheel(self, pos):
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            return (0, 0, 0)
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        if pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)
     
     
    """
    Generate a rainbow color cycle and display it on the pixels.

    Args:
        wait (float): The time to wait between each color change, in seconds.

    Returns:
        None
    """     
    def rainbow_cycle(self, wait):
        for j in range(255):
            for i in range(self.NUM_LEDS):
                rc_index = (i * 256 // self.NUM_LEDS) + j
                self.pixels_set(i, self.wheel(rc_index & 255))
            self.pixels_show()
            time.sleep(wait)
         
    """
    Get the next color from the predefined list of colors.

    Returns:
        tuple: A tuple of three integers representing the RGB color values.
    """            
    def getNextColor(self):
        self.colorIndex = self.colorIndex + 1
        
        if self.colorIndex > self.NUMBER_OF_COLORS - 1:
            self.colorIndex = 0
            
        return self.COLORS[self.colorIndex]


##############################
"""
Clock class to interact with DS1302 RTC module.

Attributes:
    ds (ds1302.DS1302): DS1302 RTC object.

Methods:
    setHour(hour): Set the hour of the clock.
    setMinute(minute): Set the minute of the clock.
    setSecond(second): Set the second of the clock.
    getDateTime(): Get the current date and time from the clock.
"""
class Clock(object):

    def __init__(self):        
    
        # Initialize DS1302 RTC with specific GPIO pins
        self.ds = ds1302.DS1302(Pin(5), Pin(18), Pin(19))  # (clk, dio, cs)

        # Get current datetime from DS1302
        self.ds.date_time()

        # Set DS1302 datetime to 2024-01-01 Monday 00:00:00
        #self.ds.date_time([2024, 12, 19, 4, 10, 34, 00])  # (year,month,day,weekday,hour,minute,second)
        
    def setHour(self, hour):           
        self.ds.hour(hour)
        
    def setMinute(self, minute):           
        self.ds.minute(minute)
        
    def setSecond(self, second):           
        self.ds.second(second)        

    def getDateTime(self):    

        datetime = self.ds.date_time()
        return datetime    

##############################
    
class OledDisplay(object):

    def __init__(self): 
        #====== setup the I2C communication
        i2c = I2C(0, sda=Pin(20), scl=Pin(21))

        # Set up the OLED display (128x64 pixels) on the I2C bus
        # SSD1306_I2C is a subclass of FrameBuffer. FrameBuffer provides support for graphics primitives.
        # http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
        self.oled = ssd1306.SSD1306_I2C(128, 64, i2c)

    """
    Clear the display by filling it with white

    Args:
        self (object): Instance of the OLED 

    Returns:
        None
    """
    def oledClearWhite(self):
        # Clear the display by filling it with white and then showing the update
        self.oled.fill(1)
        self.oled.show()
        time.sleep(1)  # Wait for 1 second

    """
    Clear the display by filling it with black

    Args:
        self (object): Instance of the OLED 

    Returns:
        None
    """
    def oledClearBlack(self):
        # Clear the display again by filling it with black
        self.oled.fill(0)
        self.oled.show()

    """
    Display date and time on the OLED screen.

    Args:
        year (int): The year.
        month (int): The month.
        day (int): The day.
        hour (int): The hour.
        minute (int): The minute.
        sec (int): The second.

    Returns:
        None
    """

    def show(self, year, month, day, hour, minute, sec, sensor):
        
        showDate = "{:0>2}/{:0>2}/{:0>2}".format(day,month,year)
        showTime = "{:0>2}:{:0>2}:{:0>2}".format(hour,minute,sec)
        
        print("Time: " + showTime)
        
        d = sensor.read()
               
        # clear 
        self.oledClearBlack()

        # Display text on the OLED screen
        self.oled.text('Date: ' + showDate, 0, 0)   
        self.oled.text('Time: ' + showTime, 0, 16)
        self.oled.text('Temp: ' + str(d[0]) + " C", 0, 32)         
        self.oled.text('Humidity: ' + str(d[1]) + "%", 0, 48)
        
        self.oled.show()

##############################
    
class ServoMotor(object):

    def __init__(self): 
        # Initialize PWM on pin 16 for servo control
        self.servo = machine.PWM(machine.Pin(16))
        self.servo.freq(50)  # Set PWM frequency to 50Hz, common for servo motors

    """
    Maps a value from one range to another.
    This function is useful for converting servo angle to pulse width.

    Args:
        x (int): The input value to be mapped.
        in_min (int): The minimum value of the input range.
        in_max (int): The maximum value of the input range.
        out_min (int): The minimum value of the output range.
        out_max (int): The maximum value of the output range.

    Returns:
        int: The mapped value.
    """
    def interval_mapping(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    """
    Moves the servo to a specific angle.
    The angle is converted to a suitable duty cycle for the PWM signal.

    Args:
        angle (int): The angle to move the servo to.

    Returns:
        None
    """    
    def servo_write(self, angle):
        pulse_width = self.interval_mapping(
            angle, 0, 180, 0.5, 2.5
        )  # Map angle to pulse width in ms
        duty = int(
            self.interval_mapping(pulse_width, 0, 20, 0, 65535)
        )  # Map pulse width to duty cycle
        self.servo.duty_u16(duty)  # Set PWM duty cycle

    """
    Chime the gong.

    Args:
        volume (int): Volume level, must be between 1 and 4.

    Returns:
        None
    """
    def chime(self, volume):
        
        if (volume > 0):
                    
            if (volume == 1):
                swingSpeed = 50
                
            if (volume == 2):
                swingSpeed = 30
                
            if (volume == 3):
                swingSpeed = 15
                
            if (volume == 4):
                swingSpeed = 0                
                            
            print("SWING: " + str(swingSpeed))
            
            for angle in range(120):
                self.servo_write(angle)
                time.sleep_ms(0)  # Short delay for smooth movement
                
            for angle in range(120,140):
                self.servo_write(angle)
                time.sleep_ms(swingSpeed)  # Short delay for smooth movement

            # Sweep the servo back from 180 to 0 degrees
            for angle in range(140, -1, -1):
                self.servo_write(angle)
                time.sleep_ms(40)  # Short delay for smooth movement
            

    def hourlyChime(self, hour, volume):
              
        #if (hour == 0):
        #    hour = 12 # Strike 12 at midnight
        #    
        #if (hour > 12):
        #    hour = hour - 12 # convert from 24 to 12 hour clock to reduce the number of dongs
        #
        #for x in range(hour):
        #    print("Dong " + str(x))
        #
        # moved out of loop so that it only dongs once
        self.chime(volume)
         
##############################

"""
A class to represent a button connected to a GPIO pin.

Args:
    pinNumber (int): The number of the GPIO pin connected to the button.

Attributes:
    button (Pin): An instance of the Pin class representing the button pin.
"""           
class Button(object):

    
    def __init__(self, pinNumber):     
        # Set input pin to read the button state
        self.button = Pin(pinNumber, Pin.IN)


class Candle(object):
    
    def __init__(self, pin):   
        self.led = Pin(pin, Pin.OUT)
        
    def on(self):
        self.led.value(1)
        
    def off(self):
        self.led.value(0)
           
    def flicker(self):
        for x in range(50):
            rnd = random.randrange(1, 100)
            sleep = rnd * 0.0001
            self.off()
            time.sleep(sleep)
            self.on()
            time.sleep(sleep)
        
           
"""
A class representing a volume button.

Attributes:
    pinNumber (int): The pin number of the button.
    button (Pin): The Pin object representing the button.
    led (Pin): The Pin object representing an onboard LED 
    led1 (Pin): The Pin object representing an onboard LED .
    led2 (Pin): The Pin object representing an onboard LED
    led3 (Pin): The Pin object representing an onboard LED 
    led4 (Pin): The Pin object representing an onboard LED 
"""          
class VolumeButton(Button):

    def __init__(self, pinNumber):
        
        super().__init__(pinNumber)
        
        # Initialize the onboard LED of the Raspberry Pi Pico W
        self.led = Pin('LED', Pin.OUT)

        # Initialize the onboard LED of the Raspberry Pi Pico W
        self.led1 = Pin(8, Pin.OUT)
        self.led2 = Pin(9, Pin.OUT)
        self.led3 = Pin(10, Pin.OUT)
        self.led4 = Pin(11, Pin.OUT)

    def volume(self, volume, servo):
        
        MAX_VOLUME = 4
        
        if self.button.value() == 1:  # Check if the button is pressed
            volume = volume + 1
            
            if (volume > MAX_VOLUME):
                volume = 0
                
            print ("Volume: " + str(volume))
                
            if (volume == 0):
                    self.led1.value(0)  
                    self.led2.value(0)
                    self.led3.value(0)
                    self.led4.value(0)
                    
            elif (volume == 1):
                    self.led1.value(1)  
                    self.led2.value(0)
                    self.led3.value(0)
                    self.led4.value(0)

            elif (volume == 2):
                    self.led1.value(1)  
                    self.led2.value(1)
                    self.led3.value(0)
                    self.led4.value(0)

            elif (volume == 3):
                    self.led1.value(1)  
                    self.led2.value(1)
                    self.led3.value(1)
                    self.led4.value(0)

            elif (volume == 4):
                    self.led1.value(1)  
                    self.led2.value(1)
                    self.led3.value(1)
                    self.led4.value(1)
                    

            self.led.value(1)  # Turn on the LED and start a test chime      
            servo.chime(volume)
            self.led.value(0)  # Turn off the LED                
        
        return volume

"""
HourButton class inherits from Button class.

Methods:
    incrementHour(clock, hour): Increments the hour by 1 if the button is pressed.

Args:
    clock (Clock): Clock object that holds the current hour.
    hour (int): Current hour value.

Returns:
    None
"""  
class HourButton(Button):

    def incrementHour(self, clock, hour):
        if self.button.value() == 1:  # Check if the button is pressed    
            hour = hour + 1
            
            if hour == 24:
                hour = 0
                
            clock.setHour(hour)

"""
MinuteButton class inherits from Button class.

Methods:
    incrementMinute(clock, hour): Increments the minute by 1 if the button is pressed.

Args:
    clock (Clock): Clock object that holds the current minute.
    hour (int): Current minute value.

Returns:
    None
"""             
class MinuteButton(Button):

    def incrementMinute(self, clock, minute):
        if self.button.value() == 1:  # Check if the button is pressed    
            minute = minute + 1
            
            if minute == 60:
                minute = 0
                
            clock.setMinute(minute)

"""
SecondButton class inherits from Button class.

Methods:
    zeroSecond(clock): Clears (zeros) the second if the button is pressed.

Args:
    clock (Clock): Clock object that holds the current second.

Returns:
    None
"""  
class SecondButton(Button):

    def zeroSecond(self, clock):
        if self.button.value() == 1:  # Check if the button is pressed               
            clock.setSecond(0)

def paintSeconds(minute, sec, neoPixel, color):

    if (sec == 0):
        color = neoPixel.getNextColor()
        
    if (minute in [59] and sec < 45):
        neoPixel.rainbow_cycle(0)
    elif (minute in [14, 29, 44]):
        neoPixel.color_chase(color, 0)
         
    neoPixel.tick(color, sec)
   
    return color
    
# Continuously display current datetime every second and chime hourly
def main():
    clock = Clock()
    sensor = TemperatureHumiditySensor()
    
    photoResistor = PhotoResistor()

    candleLeft = Candle(27)
    candleRight = Candle(22)
    
    display = OledDisplay()

    display.oledClearWhite()
    display.oledClearBlack()

    servoMotor = ServoMotor()

    neoPixel = NeoPixelRing()

    neoPixel.pixels_fill(NeoPixelRing.BLACK)

    color = neoPixel.getNextColor()

    button1 = VolumeButton(17)
    button2 = HourButton(15)
    button3 = MinuteButton(12)
    button4 = SecondButton(13)

    volume = 4

    while True:
        
        datetime = clock.getDateTime()
        
        year = datetime[0]
        month = datetime[1]
        day = datetime[2]
        
        hour = datetime[4]
        minute = datetime[5]
        sec = datetime[6]
        
        display.show(year, month, day, hour, minute, sec, sensor)
        
        if (hour in [9,10,11,12,13,14,15,16,17,18,19,20,21,22]):
            
            if (photoResistor.isDark()):
                candleRight.on()
                candleLeft.on()                
                color = paintSeconds(minute, sec, neoPixel, color)
            else:
                candleRight.off()
                candleLeft.off()
                neoPixel.pixels_fill(NeoPixelRing.BLACK)
                neoPixel.pixels_show()
                
            if (minute == 0 and sec == 0):
                servoMotor.hourlyChime(hour, volume)
                neoPixel.pixels_fill(NeoPixelRing.BLACK)
        else:
            neoPixel.pixels_fill(NeoPixelRing.BLACK)
            neoPixel.pixels_show()
            candleRight.off()
            candleLeft.off() 
            
        volume = button1.volume(volume, servoMotor)
        button2.incrementHour(clock, hour)
        button3.incrementMinute(clock, minute)
        button4.zeroSecond(clock)
        
        time.sleep(0.5)
    
if __name__ == "__main__":
    main()    
