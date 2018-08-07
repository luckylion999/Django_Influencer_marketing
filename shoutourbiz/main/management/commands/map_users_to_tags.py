import os
import sys
import time
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from main.models import IgUsers, IgUserTags, TwUsers, TwUserKeywords
from main.utils import _calculate_cpm

logging.basicConfig(level=logging.ERROR, filename="map_users_to_tags.log", filemode="a+",
                        format="%(asctime)-15s %(message)s")
timekeeper = time.time()

def _map(network, ndx1, ndx2):

	if network == 'ig':
		user_tags = IgUserTags.objects.all()[ndx1:ndx2]
	else:
		user_tags = TwUserKeywords.objects.all()[ndx1:ndx2]

	network_map = {'ig': IgUsers, 'tw': TwUsers}
	Model = network_map[network]

	ndx = 0
	for tag in user_tags:

		if ndx % 20 == 0:
			if network == 'ig':
				logging.error('#{0}: {1}'.format(ndx + ndx1, tag.hashtag))
			elif network == 'tw':
				logging.error('#{0}: {1}'.format(ndx + ndx1, tag.keyword))
			
		ndx += 1

		if network == 'ig':
			if tag.iguser:
				logging.error('{0} user #{1} already mapped. Continuing...'.format(network, ndx + ndx1))
				continue
		else:
			if tag.twuser:
				logging.error('{0} user #{1} already mapped. Continuing...'.format(network, ndx + ndx1))
				continue

		user = Model.objects.filter(userid=tag.userid).first()
		if not user:
			continue
		if network == 'ig':
			tag.iguser = user
		else:
			tag.twuser = user

		tag.save()

	m, s = divmod(time.time() - timekeeper, 60)
	h, m = divmod(m, 60)
	logging.error('Ran for %dh: %02dm: %02ds' % (h, m, s))

class Command(BaseCommand):

	def add_arguments(self, parser):
		parser.add_argument('network', nargs=1)
		parser.add_argument('ndx1', nargs=1, type=int)
		parser.add_argument('ndx2', nargs=1, type=int)

	def handle(self, *args, **options):
		if options['ndx1'][0] is not None and options ['ndx2'][0] is not None and \
				options['network'][0] is not None:

			_map(options['network'][0], options['ndx1'][0], options['ndx2'][0])

		else:
			logging.error('Uh oh, unable to parse arguments...')