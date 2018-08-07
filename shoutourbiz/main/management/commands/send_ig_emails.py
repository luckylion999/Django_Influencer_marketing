from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

import requests
import re
import os
import time
import furl
import json
import datetime

class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument('ndx1', nargs=1, type=int)
		parser.add_argument('ndx2', nargs=1, type=int)

	def handle(self, *args, **options):
		if options['ndx1'][0] is not None and options ['ndx2'][0] is not None:
			hashtags = _get_data(options['ndx1'][0], options['ndx2'][0])
			_main_process(hashtags)
		else:
			print 'Uh oh, unable to parse indices...'