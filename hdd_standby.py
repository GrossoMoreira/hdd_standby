#!/usr/bin/env python3

import datetime
import re
import subprocess
import time
import signal
import sys

TIMEOUT = datetime.timedelta(minutes=3)

DISKSTATS_FILE = '/proc/diskstats'
DISKNAME_REGEX = r'sd[a-z]'

def issue_standby(disk):
	subprocess.check_output(['hdparm', '-y', '/dev/' + disk])

def get_disk_stats(disk):
	with open(DISKSTATS_FILE , 'r') as f:
		for stat in f:
			columns = stat.split()
			dev = columns[2]
			if dev == disk:
				return stat

	raise Exception('Disk ' + disk + ' not found under ' + DISKSTATS_FILE + '.')

class DiskController:
	def __init__(self, disk):
		self.disk = disk
		self.laststats = get_disk_stats(self.disk)
		self.lastchange = datetime.datetime.now()

	def run(self):
		while True:
			currstats = get_disk_stats(self.disk)
			now = datetime.datetime.now()

			if currstats != self.laststats:
				self.laststats = currstats
				self.lastchange = now
			elif now > self.lastchange + TIMEOUT:
				issue_standby(self.disk)

			time.sleep(60)

def signal_handler(sig, frame):
	print('Stopped.')
	sys.exit(0)

if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal_handler)

	if len(sys.argv) != 2:
		print('You must provide one argument, which is the name of the target device (eg. sda) without /dev')
		sys.exit(-1)

	disk = sys.argv[1]

	if not re.match(DISKNAME_REGEX, disk):
		print('Invalid device name! Must match expression %s', DISKNAME_REGEX)
		sys.exit(-2)

	dc = DiskController(disk)
	dc.run()

