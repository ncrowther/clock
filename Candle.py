# LED Candle animation for microypthon on esp8266

# Copyright 2018 Fritscher
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Values for the Gaussian distribution are taken from Eric's comment on https://cpldcpu.wordpress.com/2016/01/05/reverse-engineering-a-real-candle/
import time
import uos
import math
import machine, neopixel

# number of leds in the strip
LED_COUNT = 16
# base color
r = 255
g = 120
b = 10

np = neopixel.NeoPixel(machine.Pin(16), LED_COUNT) #28

def show():
   np.write()

def Color(r, g, b):
    return (int(r), int(g), int(b))

def setPixelColor(i, color):
    np[i] = color

def wait(ms):
   time.sleep(ms/1000.0)

def randint(min, max):
    return min + int(int.from_bytes(uos.urandom(2), 10) / 65536.0 * (max - min + 1))

def c_brightness(c, brightness):
    return max(0, min(c * brightness / 100, 255))

class LED_light(object):
    def __init__(self, pos):
        self.time = 0
        self.pos = pos

    def update(self, delta):
        self.time = self.time - delta
        if self.time <= 0:
            self.random_mode()
            self.random_duration()

    def set_brightness(self, brightness):
        setPixelColor(self.pos, Color(c_brightness(r, brightness), c_brightness(g, brightness), c_brightness(b, brightness)))


    def random_mode(self):
        # Probability Random LED Brightness
        # 50% 77% â€“  80% (its barely noticeable)
        # 30% 80% â€“ 100% (very noticeable, sim. air flicker)
        #  5% 50% â€“  80% (very noticeable, blown out flame)
        #  5% 40% â€“  50% (very noticeable, blown out flame)
        # 10% 30% â€“  40% (very noticeable, blown out flame)
        brightness = 0
        r = randint(0, 100)
        if r < 50:
            brightness = randint(77, 80)
        elif r < 80:
            brightness = randint(80, 100)
        elif r < 85:
            brightness = randint(50, 80)
        elif r < 90:
            brightness = randint(40, 50)
        else:
            brightness = randint(30, 40)
        self.set_brightness(brightness)

    def random_duration(self):
        # Probability Random Time
        # 90% 20 ms
        #  3% 20 â€“ 30 ms
        #  3% 10 â€“ 20 ms
        #  4%  0 â€“ 10 ms
        r = randint(0, 100)
        if r < 90:
            self.time = 20
        elif r < 93:
            self.time = randint(20, 30)
        elif r < 96:
            self.time = randint(10, 20)
        else:
            self.time = randint(0, 10)

def main():
    candles = [LED_light(i) for i in range(LED_COUNT)]
    while True:
        now = time.ticks_ms()
        [l.update(now) for l in candles]
        show()
        wait(60)

main()

