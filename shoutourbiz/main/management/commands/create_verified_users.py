"""
This module stores the calculate_cpm command, which 
calculates the CPM of all verified users and stores that
value in the IgUsersCPM model.
"""

import os
import sys
import time

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

import csv

from main.models import VerifiedUserAccounts

class Command(BaseCommand):

	def handle(self, *args, **options):

		header = 0;

		with open('verified.csv') as f:
			reader = csv.reader(f, delimiter=';')

			for row in reader:
				print row
				if header == 0:
					header += 1
					continue
				

				try:
					_, created = VerifiedUserAccounts.objects.get_or_create(
	                	email = row[0],
	                	network = row[1],
	                	account_id = row[2],
	                	id = row[3],
	                	price = row[4],
	                	note = row[5],
	                	cpm = row[6]
	                )
				except IntegrityError as e:
					print e
					print row
					continue