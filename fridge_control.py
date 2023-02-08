import glob
import time
import datetime
import RPi.GPIO as GPIO
import logging
from db_control import Chamber

## Parameter change by users
# day time
START_TIME = datetime.time(5, 0, 0)
# night time
END_TIME = datetime.time(22, 59, 59)
# day time temperature highest
DAY_TEMP_HIGH = 26
# day time temperature lowest
DAY_TEMP_LOW = 25.5
# night time temperature highest
NIGHT_TEMP_HIGH = 17.5
# night time temperature lowest
NIGHT_TEMP_LOW = 17.3


## default raspberry pi setup
GPIO.setmode(GPIO.BCM)
# GPIO for relay switch
TEMP_GPIO = 21
GPIO.setup(TEMP_GPIO, GPIO.OUT)
# GPIO initial state is off
GPIO_STATE = 0


## temperature reading directory
# note that by default, GPIO4 is w1 connection
base_dir = '/sys/bus/w1/devices/'
# ds18b20 w1 directory always starts with 28_xxxxxx
device_folder = glob.glob(base_dir + '28*')[0]
# w1_slave file containing raw acsii reading
device_file = device_folder + '/w1_slave'

## logging info
logging.basicConfig(filename='/home/pi/Fridge-to-Incubator/fridge.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')



def time_in_range(start, end, current):
	"""Return whether current time is in range [start, end]"""
	return start <= current <= end


def read_temp_raw():
	"""Read w1 ds18b20 sensor file"""
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines


def read_temp():
	"""Check if sensor file exist, get readings"""
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
	logging.info(f"Current temperature: {temp_c}")
	return temp_c


def relay_temp_switch(on_off):
	"""Control relay switch"""
	if on_off == "ON":
		GPIO.output(TEMP_GPIO, GPIO.HIGH)
		logging.info("Compressor ON")
		return 1
	else:
		GPIO.output(TEMP_GPIO, GPIO.LOW)
		logging.info("Compressor OFF")
		return 0


## Run the script
logging.debug("Start script.")


# init connection to sensor
max_try = 0
# temperature relay switch status
compressor_switch = 0
light_switch = 0

try:

	logging.debug("Start loop")

	while True:
		current_time = datetime.datetime.now().time()
		print(current_time)

		try:
			current_temp = read_temp()
			print(current_temp)

		except Exception as e:
			print(e)
			max_try += 1
			logging.warning(f"Sensor fail, retry attempt: {max_try}")
			if max_try >= 3:
				GPIO.output(TEMP_GPIO, GPIO.LOW)
				logging.critical("Script will now terminate due to error")
				logging.critical(e)
				break
			time.sleep(60)

			continue

		if time_in_range(START_TIME, END_TIME, current_time):
			print("DAYTIME")
			logging.info("DAYTIME")
			if current_temp > DAY_TEMP_HIGH:
				compressor_switch = relay_temp_switch("ON")
			if current_temp <= DAY_TEMP_LOW:
				compressor_switch = relay_temp_switch("OFF")

		else:
			print("NIGHTTIME")
			logging.info("NIGHTTIME")
			if current_temp > NIGHT_TEMP_HIGH:
				compressor_switch = relay_temp_switch("ON")
			if current_temp <= NIGHT_TEMP_LOW:
				compressor_switch = relay_temp_switch("OFF")

		# Readings to be saved in SQL database
		readings = ("SmallFridge", time.strftime('%Y-%m-%d %H:%M:%S'), current_temp, light_switch, compressor_switch)

		# Output tuple(Device, DateTime, EC, Humidity, pH, Temperature)
		record = Chamber("GerminationFridge")

		record.insert_reading_values(readings)

		time.sleep(60)

except Exception as e:
	print(e)
	logging.error("Outside loop")
	logging.error(e)

finally:
	GPIO.output(TEMP_GPIO, GPIO.LOW)
	logging.error("INTERRUPTED. SWITCH OFF RELAY NOW!")
	GPIO.cleanup()
	logging.debug("Cleanup GPIO complete.")
