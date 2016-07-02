#!/usr/bin/env python

import time
import urllib2
import json
import sys
import random
import logging
import os

from neopixel import *

__author__ = "Florian Wallburg"
__copyright__ = "Copyright 2016, Florian Wallburg"
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Florian Wallburg"
__email__ = "florian.wallburg@web.de"
__status__ = "Development"

# Logging configuration
LOGGING_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),'logging.log')
logging.basicConfig(filename=LOGGING_FILE,level=logging.INFO,
	format='%(asctime)s %(levelname)s: %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S')

# LED strip configuration:
LED_COUNT      = 32       # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 100     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Pi-hole configuration:
PIHOLE         = "http://10.0.1.30/admin/"
PERCENTPERLED  = float(100 / LED_COUNT)

# Define functions which animate LEDs in various ways.
def showPercent(strip, percentage, wait_ms=50):
	""" Draw blocked ads as percentage  """
	leds = int(percentage / PERCENTPERLED)
	midrange_low = 10
	midrange_high = 30

	logging.debug("LEDs to use -> %d" % leds)

	# Magenta color as default
	led_color = Color(255,0,255)

        if 0 < percentage <= midrange_low:
		logging.debug('percentage < %d' % midrange_low)
		# Green
		led_color = Color(255,0,0)
	elif midrange_low < percentage < midrange_high:
		logging.debug('percentage between %d and %d' % (midrange_low, midrange_high))
		# Yellow
		led_color = Color(255,255,0)
        else:
		logging.debug('percentage above %d' % midrange_high)
		# Red
		led_color = Color(0,255,0)

	if leds == 0:
		leds = LED_COUNT

	for i in range(leds):
		logging.debug('led %d light up' % i)
		strip.setPixelColor(i, led_color)
               	strip.show()
		time.sleep(wait_ms/1000.0)


def colorWipe(strip, color, wait_ms=50):
	"""Wipe color across display a pixel at a time."""
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, color)
		strip.show()
		time.sleep(wait_ms/1000.0)


# Main program logic follows:
if __name__ == '__main__':
	# Create NeoPixel object with appropriate configuration.
	strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
	# Intialize the library (must be called once before other functions).
	strip.begin()

	logging.debug('percent per LED -> %d' % PERCENTPERLED)

	try:
		url = PIHOLE + "api.php"
		result = urllib2.urlopen(url, timeout = 10).read()
		json = json.loads(result)
		ads_blocked_percent = float(json['ads_percentage_today'])
		#ads_blocked_percent = random.randint(0, 100)
		#logging.debug('Ads blocked -> %d percent' % ads_blocked_percent)
		logging.info('Ads blocked: %d percent' % ads_blocked_percent)

		# Show some LED magic
		colorWipe(strip, Color(0, 0, 0))
		showPercent(strip, ads_blocked_percent)
	except:
		logging.warn('Pi-Hole not found!')
		logging.warn('Unexpected error: %s' % sys.exc_info()[0])
    		raise
