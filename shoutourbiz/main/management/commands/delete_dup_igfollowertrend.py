from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db import IntegrityError

import requests
import re
import os
import time
import json
import datetime
import random
import logging

from bs4 import BeautifulSoup
from pprint import pprint

from main.models import IgUsers, IgUserTags, IgFollowerTrend

def _get_data(nxd1, ndx2):
	users = IgUsers.objects.all()[nxd1:ndx2]
	return users

class Command(BaseCommand):

	def handle(self, *args, **options):

		total_num = IgUsers.objects.all().count()
		print 'There are {0} items...'.format(total_num)

		current_ndx = 0
		num_steps = 100
		while current_ndx < total_num:
			users = _get_data(current_ndx, current_ndx + num_steps)
			print '------- ndx: {0} | id={1}'.format(current_ndx, users[0].id)

			for user in users:

				if current_ndx % 100 == 0:
					print 'ndx: {0} | {1} | {2}'.format(current_ndx, user.id, user.username)

				trends = user.igfollowertrend_set.all()
				if len(trends) <= 1:
					current_ndx += 1
					continue

				# '2017-06-19'
				#print 'deleting 2017-06-19'
				trends_one = trends.filter(date='2017-06-19')
				for i in range(len(trends_one)):
					if i > 0:
						trends[i].delete()

				# '2017-07-01'
				#print 'deleting 2017-07-01'
				trends_two = trends.filter(date__range=['2017-07-01', '2017-07-02'])
				for i in range(len(trends_two)):
					if i > 0:

						tmp_trend = IgFollowerTrend.objects.get(pk=trends_two[i].id)
						try:
							tmp_trend.delete()
						except Exception as e:
							import pdb; pdb.set_trace()
							print 'e'


				current_ndx += 1