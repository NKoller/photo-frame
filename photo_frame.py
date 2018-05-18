# -----------------------------------------------------------------------------------
#   photo_frame - Nadav Koller
#   This program randomly chooses JPG files from /media/pi/USB/ and displays them
#   using feh. It follows schedules specified in /media/pi/USB/Settings.txt, turning
#   the screen off during the times that the file specifies.
# -----------------------------------------------------------------------------------

import time
from os import listdir
from random import random
import subprocess

USB_DIR = "/media/pi/USB/"
PICTURE_DELAY = 0
SLEEP_DELAY = 1800  # Half hour
INPUT_DELAY = 3
BUFFER_RATIO = 0.33
settings = []
is_weekend = True
directory = {}
len_directory = 0
pic_buffer = {}
pid = ""
background_pid = ""
t_minus = 2


# Updates the image buffer that keeps tracks of all recently displayed pictures.
# This is used to ensure the same picture isn't displayed several times in during
# a short period.

def update_buffer(new_num):
	global pic_buffer
	free_pic = -1
	for pic in pic_buffer:
		pic_buffer[pic] += 1
		if pic_buffer[pic] >= len_directory * BUFFER_RATIO:
			free_pic = pic
	if free_pic != -1:
		del pic_buffer[free_pic]
	pic_buffer[new_num] = 0


# Modifies file names to ensure that they can be used in bash commands with no errors.

def fix_name(name):
	if ' ' in name:
		fixed_name = ""
		for char in name:
			if char == ' ' or char == '(' or char == ')' or char == '-':
				fixed_name += "\\"
			fixed_name += char
		return fixed_name
	else:
		return name


# Chooses a random picture and displays it using shell commands. Closes
# previously opened pictures.

def display():
	global pid
	global t_minus
	output = False
	is_picture = False

	while is_picture == False:
		while True:
			rand_num = int(random()*len_directory)
			if rand_num not in pic_buffer:
				break

		for folder in directory:
			if rand_num - len(directory[folder]) < 0:
				folder_name = fix_name(folder)
				file_name = fix_name(directory[folder][rand_num])

				is_picture = (".JPG" in file_name)
				if is_picture:
            				# Kill picture 1
					if t_minus > 0:
						t_minus -= 1
					else:
						if pid == background_pid:
							output = True
						else:
							output = subprocess.call("kill " + pid, shell = True)
						"""if output == False:
							print("successful kill " + pid)
						else:
							print("failed kill " + pid)"""
					# Get PID of picture 2 for killing next time
					pid = subprocess.Popen(["pidof", "feh"], stdout=subprocess.PIPE).communicate()[0].split(' ')[0]
					# Display picture 3 (zoom, -x no window, -F full screen, -Y no cursor, no error messages)
					subprocess.call("feh -Z -x -F -Y -q " + USB_DIR + "Pictures/" + folder_name + "/" + file_name + " &", shell = True)
				break
			rand_num -= len(directory[folder])

	update_buffer(rand_num)
	return output


# Controls the program flow. Reads input from the USB when necessary,
# chooses when to display pictures or start sleep mode.

def main(need_input):
	if need_input:
		try:
			# Get setting input
			settings_file = open(USB_DIR + "Settings.txt", "r")
			new_settings = settings_file.readlines()
			settings_file.close()
			global settings
			settings = new_settings

			# Get picture directory
			folders = listdir(USB_DIR + "Pictures")
			new_directory = {}
			new_len_directory = 0
			for folder in folders:
				new_directory[folder] = listdir(USB_DIR + "Pictures/" + folder)
				new_len_directory += len(new_directory[folder])
			global directory
			directory = new_directory
			global len_directory
			len_directory = new_len_directory
			#print ("got input")		
		except IOError:
			global t_minus
			t_minus = 2
			#print ("no USB")
			return INPUT_DELAY, True

	global PICTURE_DELAY 
	PICTURE_DELAY = int(settings[12].split(':')[1])
	
	delay = PICTURE_DELAY

	start_time = int(settings[1].split(':')[1]) * 60 + int(settings[1].split(':')[2])
	end_time = int(settings[2].split(':')[1]) * 60 + int(settings[2].split(':')[2])
	start_time2 = int(settings[5].split(':')[1]) * 60 + int(settings[5].split(':')[2])
	end_time2 = int(settings[6].split(':')[1]) * 60 + int(settings[6].split(':')[2])
	start_time3 = int(settings[9].split(':')[1]) * 60 + int(settings[9].split(':')[2])
	end_time3 = int(settings[10].split(':')[1]) * 60 + int(settings[10].split(':')[2])
	local_time = time.localtime(time.time())
	current_time = local_time[3] * 60 + local_time[4]

	if need_input or current_time < 30:
		need_input = check_day(local_time)

	if not need_input:
		if not is_weekend:
			if (start_time <= current_time and current_time < end_time) or (start_time2 <= current_time and current_time < end_time2):
				need_input = display()
			else:
				delay = SLEEP_DELAY
				#print ("sleep")
		else:
			if start_time3 <= current_time and current_time < end_time3:
				need_input = display()
			else:
				delay = SLEEP_DELAY
				#print ("sleep")

	if need_input:
		return INPUT_DELAY, True
	else:
		return delay, False


# Returns true if the current day is a "holiday" as specified in
# media/pi/USB/Holidays.txt. This is important for knowing which
# user schedule to follow.

def check_day(time):
	global is_weekend

	if time[6] > 4:
		is_weekend = True
	else:
		try:
			holidays_file = open(USB_DIR + "Holidays.txt", "r")
			while True:
				try:
					if int(holidays_file.readline()) == time[0]:
						break
				except ValueError:
					continue
			while True:
				line = holidays_file.readline()
				if line == "-\r\n":
					is_weekend = False
					break
				if int(line.split('/')[0]) == time[1] and int(line.split('/')[1]) == time[2]:
					is_weekend = True
					break
			holidays_file.close()
		except IOError:
			return True
	return False


# Loops the main function using the delay times it returns. Uses
# shell commands to turn the screen on/off when specified by main.

if __name__ == "__main__":
	need_input = True
	asleep = False
	subprocess.call("feh -Z -x -F -Y -q /home/pi/Pictures/background.png &", shell = True)
	background_pid = subprocess.Popen(["pidof", "feh"], stdout=subprocess.PIPE).communicate()[0]
	time.sleep(2)
	while True:
		#print("run")
		output = main(need_input)
		need_input = output[1]
		
		if asleep == False and output[0] == SLEEP_DELAY:
			asleep = True
			subprocess.call("tvservice -o", shell = True)
		elif asleep and output[0] != SLEEP_DELAY and not need_input: #"not need_input" excludes INPUT_DELAY
			asleep = False
			subprocess.call("tvservice -p", shell = True)
			subprocess.call("sudo chvt 6", shell = True)
			subprocess.call("sudo chvt 7", shell = True)

		time.sleep(output[0])
