import Adafruit_DHT
import thingspeak
import time
import secrets as Secrets
from datetime import datetime

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

import Image
import ImageDraw
import ImageFont

import RPi.GPIO as GPIO    # Import Raspberry Pi GPIO library
from time import sleep     # Import the sleep function from the time module
from gpiozero import CPUTemperature

DHT_LED_PIN = 4
THINGSPEAK_LED_PIN = 22

GPIO.setwarnings(False)    # Ignore warning for now
GPIO.setmode(GPIO.BCM)   # Use physical pin numbering
GPIO.setup(DHT_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(THINGSPEAK_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
DHT_SENSOR = Adafruit_DHT.AM2302
DHT_PIN = 17

last_dht_temperature = 0.0
last_dht_humidity = 0.0

last_dht_read_timestamp = 0
dht_read_timeout = 60 * 1000

RST = None

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
cpu = CPUTemperature()

def initOled():
  disp.begin()
  disp.clear()
  disp.display()

def showOled():
  global last_dht_temperature
  global last_dht_humidity

  width = disp.width
  height = disp.height

  image = Image.new('1', (width, height))
  draw = ImageDraw.Draw(image)

  draw.rectangle((0, 0, width, height), outline=0, fill=0)

  padding = 0
  top = padding
  bottom = height - padding
  # Move left to right keeping track of the current x position for drawing shapes.
  x = 0

  font = ImageFont.truetype(Secrets.filesPath + 'VCR_OSD_MONO_1.ttf', 20)
  draw.text((x, top),         str(last_dht_temperature) + "C",  font=font, fill=255)

  fontSmall = ImageFont.truetype(Secrets.filesPath + 'VCR_OSD_MONO_1.ttf', 14)
  draw.text((x, top + 20),    "CPU " + str(round(cpu.temperature, 1)) + "C",  font=fontSmall, fill=255)

  draw.text((x, top + 40),    str(last_dht_humidity) + "%",  font=font, fill=255)

  # Icons
  imagePaste = Image.open(Secrets.filesPath + 'termometer.png')
  image.paste(imagePaste, (width - 30, top))

  # Display image.
  disp.image(image)
  disp.display()

def measure(channel):
  global last_dht_temperature
  global last_dht_humidity
  humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

  if humidity is not None and temperature is not None:
    last_dht_temperature = round(temperature, 2)
    last_dht_humidity = round(humidity, 2)
    print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
    blinkLED(DHT_LED_PIN)
    showOled()
    try:
      response = channel.update({'field1':last_dht_temperature, 'field2': last_dht_humidity})
      blinkLED(THINGSPEAK_LED_PIN)
    except:
      print("Connection failure")
  else:
    print("Failed to retrieve data from humidity sensor")

def toTimestamp(time):
  epoch = datetime.utcfromtimestamp(0)
  return (time - epoch).total_seconds() * 1000.0

def blinkLED(pin):
  GPIO.output(pin, GPIO.HIGH)
  sleep(0.2)
  GPIO.output(pin, GPIO.LOW)
  sleep(0.2)
  GPIO.output(pin, GPIO.HIGH)
  sleep(0.2)
  GPIO.output(pin, GPIO.LOW)

channel = thingspeak.Channel(id=Secrets.channel_id, write_key=Secrets.write_key)
initOled()

while True:
  now = toTimestamp(datetime.now())
  if (now - last_dht_read_timestamp >= dht_read_timeout):
    last_dht_read_timestamp = now
    measure(channel)
  sleep(1)