#!/usr/bin/env python3

import time
from urllib.request import urlopen
import json
import sys
import random
import logging
import os

import board
import neopixel

__author__ = "Florian Wallburg"
__copyright__ = "Copyright 2016, Florian Wallburg"
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Florian Wallburg"
__email__ = "florian.wallburg@web.de"
__status__ = "Development"

# Logging configuration
LOGGING_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'logging.log')
logging.basicConfig(filename=LOGGING_FILE,
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# LED strip configuration:
LED_COUNT = 8  # Number of LED pixels.
LED_PIN = board.D18  # GPIO pin connected to the pixels (must support PWM!).

# Pi-hole configuration:
PIHOLE = "http://10.0.1.30/admin/"
PERCENTPERLED = float(100 / LED_COUNT)


# Define functions which animate LEDs in various ways.
def showPercent(strip, percentage, wait_ms=50):
    """ Draw blocked ads as percentage  """
    """ 8 LEDS -> 12.5/25/37.5/50/62.5/75/87.5/100 """
    leds = int(percentage / PERCENTPERLED)
    midrange_low = 26
    midrange_high = 76

    logging.debug("LEDs to use -> %d" % leds)

    # Magenta color as default
    led_color = (255, 0, 255)

    if (0 < percentage < midrange_low):
        logging.debug('percentage < %d, color: green' % midrange_low)
        # Green
        led_color = (255, 0, 0)
    elif (midrange_low <= percentage < midrange_high):
        logging.debug('percentage between %d and %d, color: yellow' %
                      (midrange_low, midrange_high))
        # Yellow
        led_color = (255, 255, 0)
    else:
        logging.debug('percentage above %d, color: red' % midrange_high)
        # Red
        led_color = (0, 255, 0)

    if (leds == 0 or leds > LED_COUNT):
        leds = LED_COUNT

    for i in range(leds):
        logging.debug('led %d light up' % i)
        strip[i] = led_color
        strip.show()
        time.sleep(wait_ms / 1000.0)


# Reset each LED with predefined color
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(LED_COUNT):
        strip[i] = color
        strip.show()
        time.sleep(wait_ms / 1000.0)


# Mapping value from scale a to scale b
def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


# Main program logic follows:
if __name__ == '__main__':
    # Create NeoPixel object with appropriate configuration.
    strip = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=0.2)
    # Intialize the library (must be called once before other functions).
    #strip.begin()

    logging.debug('percent per LED -> %d' % PERCENTPERLED)

    try:
        url = PIHOLE + "api.php"
        result = urlopen(url, timeout=10).read()
        json = json.loads(result.decode('utf-8'))
        ads_blocked_percent = float(json['ads_percentage_today'])
        logging.info('Ads blocked: %.2f percent' % ads_blocked_percent)

        # Show some LED magic
        colorWipe(strip, (0, 0, 0))
        ads_blocked_percent = map(ads_blocked_percent, 0, 20, 0, 100)
        logging.debug('Mapping to ads blocked: %.2f' % ads_blocked_percent)
        showPercent(strip, ads_blocked_percent)
    except:
        logging.warn('Pi-Hole not found!')
        logging.warn('Unexpected error: %s' % sys.exc_info()[0])
        raise
