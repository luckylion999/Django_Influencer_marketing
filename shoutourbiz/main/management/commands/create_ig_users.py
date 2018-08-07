import os
import sys
import time

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

import csv
import pandas as pd

from main.models import IgUsers

def _read_pandas(path):

	df = pd.read_csv(path, 
		delimiter=';',
		header=0,
		)
	
	print df.head()
	print '----------------------------'

	ndx = 0
	for index, row in df.iterrows():

		try:
			user, created = IgUsers.objects.get_or_create(
				username = row['username'],
				email = row['email'])
			if created:
				user.email = row['email']
				user.emailScraped = row['emailScraped']
				user.postcount =  row['postcount']
				user.postavglike = row['postavglike']
				user.verified = row['verified']
				user.userid = row['userid']
				user.emailsent = row['emailsent']
				user.verified_acc = row['verified_acc']
				user.related_accs_scraped = row['related_accs_scraped']
				user.save()
		except Exception as e:
			print e
			print row
			continue

		if ndx % 10 == 0:
			print str(ndx)

		ndx += 1	
				
class Command(BaseCommand):

	def add_arguments(self, parser):

		parser.add_argument(
			'--path',
			default=False,
			help='Run parser with a local file, with the path specified as input'
		)
		parser.add_argument(
			'--pandas',
			default=False,
			help='Run parser using pandas, which is faster than the default Python reader'
		)

	def handle(self, *args, **options):

		if options['path']:
			path = options['path']
		else:
			raise Exception('You must input a valid path')

		start = time.time()

		if options['pandas']:
			_read_pandas(path)
		else:
			_read_default_lib(path)

		end = time.time() - start
		print 'Time ellapsed: {0}'.format(end)

		