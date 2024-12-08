from machine import Pin, I2C
import ssd1306
import ds1302
import time
import array
import rp2
import math
    
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
    
class NeoPixelRing(object):

    # Configure the number of WS2812 LEDs.
    NUM_LEDS = 16 
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
    COLORS = (WHITE, RED, WHITE, GREEN, WHITE, BLUE, CYAN, PURPLE, WHITE, BLUE)
    NUMBER_OF_COLORS = len(COLORS)

    def __init__(self): 
    
        # Create the StateMachine with the ws2812 program, outputting on pin
        self.sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(self.PIN_NUM))

        # Start the StateMachine, it will wait for data on its FIFO.
        self.sm.active(1)

        # Display a pattern on the LEDs via an array of LED RGB values.
        self.ar = array.array("I", [0 for _ in range(self.NUM_LEDS)])
        
        self.colorIndex = 0


    def pixels_show(self):
        dimmer_ar = array.array("I", [0 for _ in range(self.NUM_LEDS)])
        for i,c in enumerate(self.ar):
            r = int(((c >> 8) & 0xFF) * self.BRIGHTNESS)
            g = int(((c >> 16) & 0xFF) * self.BRIGHTNESS)
            b = int((c & 0xFF) * self.BRIGHTNESS)
            dimmer_ar[i] = (g<<16) + (r<<8) + b
        self.sm.put(dimmer_ar, 8)
        time.sleep_ms(10)

    def pixels_set(self, i, color):
        self.ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]

    def pixels_fill(self, color):
        for i in range(len(self.ar)):
            self.pixels_set(i, color)

    def clockTick(self, color, wait):
        for i in range(self.NUM_LEDS)[::-1]:
            self.pixels_set(i, color)
            time.sleep(wait)
            self.pixels_show()
        #time.sleep(0.2)
            
    def color_chase(self, color, wait):
        for i in range(NUM_LEDS)[::-1]:
            previousPixel = 0 if (i == self.NUM_LEDS-1) else i + 1
            print(i, previousPixel)
            self.pixels_set(previousPixel, self.BLACK)
            self.pixels_set(i, color)
            time.sleep(wait)
            self.pixels_show()
            
    def tick(self, color, i):
        
        pixel = ((i / 59)  * self.NUM_LEDS - 1)
        #previousPixel = 0 if (pixel >= self.NUM_LEDS-3) else pixel + 1
        print(i,pixel)
        
        pixel = math.ceil(pixel)
        
        print(pixel)
        
        #self.pixels_set(previousPixel, self.BLACK)
        self.pixels_set(pixel, color)
        self.pixels_show()
     
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
     
     
    def rainbow_cycle(self, wait):
        for j in range(255):
            for i in range(self.NUM_LEDS):
                rc_index = (i * 256 // self.NUM_LEDS) + j
                self.pixels_set(i, self.wheel(rc_index & 255))
            self.pixels_show()
            time.sleep(wait)
            
    def getNextColor(self):
        self.colorIndex = self.colorIndex + 1
        
        if self.colorIndex > self.NUMBER_OF_COLORS - 1:
            self.colorIndex = 0
            
        return self.COLORS[self.colorIndex]


##############################

class Clock(object):

    def __init__(self):        
    
        # Initialize DS1302 RTC with specific GPIO pins
        self.ds = ds1302.DS1302(Pin(5), Pin(18), Pin(19))  # (clk, dio, cs)

        # Get current datetime from DS1302
        self.ds.date_time()

        # Set DS1302 datetime to 2024-01-01 Monday 00:00:00
        #self.ds.date_time([2024, 12, 7, 6, 21, 10, 00])  # (year,month,day,weekday,hour,minute,second)

        # Set seconds to 10
        #self.ds.second(58)

    def  getDateTime(self):    

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

    def oledClearWhite(self):
        # Clear the display by filling it with white and then showing the update
        self.oled.fill(1)
        self.oled.show()
        time.sleep(1)  # Wait for 1 second

    def oledClearBlack(self):
        # Clear the display again by filling it with black
        self.oled.fill(0)
        self.oled.show()

    def showDateTime(self, date, time):

        # clear 
        self.oledClearBlack()

        # Display text on the OLED screen
        self.oled.text('Date ' + date, 0, 0)  # Display "Hello," at position (0, 0)
        #oled.text(date, 0, 16)  # Display at position (0, 16)
        
        self.oled.text('Time ' + time, 0, 32)  # Display "Hello," at position (0, 0)
        #oled.text(time, 0, 48)  # Display at position (0, 16)
        
        self.oled.show()


##############################
    
class ServoMotor(object):

    def __init__(self): 
        # Initialize PWM on pin 16 for servo control
        self.servo = machine.PWM(machine.Pin(16))
        self.servo.freq(50)  # Set PWM frequency to 50Hz, common for servo motors

    def interval_mapping(self, x, in_min, in_max, out_min, out_max):
        """
        Maps a value from one range to another.
        This function is useful for converting servo angle to pulse width.
        """
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


    def servo_write(self, angle):
        """
        Moves the servo to a specific angle.
        The angle is converted to a suitable duty cycle for the PWM signal.
        """
        pulse_width = self.interval_mapping(
            angle, 0, 180, 0.5, 2.5
        )  # Map angle to pulse width in ms
        duty = int(
            self.interval_mapping(pulse_width, 0, 20, 0, 65535)
        )  # Map pulse width to duty cycle
        self.servo.duty_u16(duty)  # Set PWM duty cycle

    def testChime(self):
                        
        # Sweep the servo from 0 to 180 degrees
        for angle in range(140):
            self.servo_write(angle)
            time.sleep_ms(100)  # Short delay for smooth movement

        # Sweep the servo back from 180 to 0 degrees
        for angle in range(140, -1, -1):
            self.servo_write(angle)
            time.sleep_ms(30)  # Short delay for smooth movement

    def chime(self):
                        
        # Sweep the servo from 0 to 180 degrees
        for angle in range(140):
            self.servo_write(angle)
            time.sleep_ms(0)  # Short delay for smooth movement

        # Sweep the servo back from 180 to 0 degrees
        for angle in range(140, -1, -1):
            self.servo_write(angle)
            time.sleep_ms(30)  # Short delay for smooth movement

    def hourlyChime(self, hour):
        
        if (hour > 12):
            hour = hour -12 # convert from 24 to 12 hour clock to reduce the number of dongs

        for x in range(hour):
            print("Dong " + str(x))                 
            self.chime()
         
##############################
            
class Button(object):

    def __init__(self):     
        # Set GPIO 17 as an input pin to read the button state
        self.button1 = Pin(17, Pin.IN)

        # Initialize the onboard LED of the Raspberry Pi Pico W
        self.led = Pin('LED', Pin.OUT)

    def testChime(self, servo):
        if self.button1.value() == 1:  # Check if the button is pressed
            self.led.value(1)  # Turn on the LED and start a test chime
            servo.testChime()
        else:
            self.led.value(0)  # Turn off the LED
            
# Continuously display current datetime every  second
clock = Clock()    
display = OledDisplay()

display.oledClearWhite()
display.oledClearBlack()

servoMotor = ServoMotor()

neoPixel = NeoPixelRing()

neoPixel.pixels_fill(NeoPixelRing.BLACK)

color = neoPixel.getNextColor()

button = Button()

while True:

    datetime = clock.getDateTime()
        
    year = datetime[0]
    month = datetime[1]
    day = datetime[2]
    
    showDate = "{:0>2}/{:0>2}/{:0>2}".format(day,month,year)

    hour = datetime[4]
    minute = datetime[5]
    sec = datetime[6]
  
    showTime = "{:0>2}:{:0>2}:{:0>2}".format(hour,minute,sec)

    display.showDateTime(showDate, showTime)
         
    if (sec == 0):
        color = neoPixel.getNextColor()
        
    reverseSecond = abs(sec - 59)        
    
    neoPixel.tick(color, reverseSecond)
      
    
    if (hour > 7 and hour <= 23) and (minute == 0 and sec == 0):
        neoPixel.rainbow_cycle(0)
        servoMotor.hourlyChime(hour)
        neoPixel.pixels_fill(NeoPixelRing.BLACK)
        
    button.testChime(servoMotor)
             
    time.sleep(1)
    
