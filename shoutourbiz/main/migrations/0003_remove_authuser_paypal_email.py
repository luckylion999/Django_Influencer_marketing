# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20170627_0827'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authuser',
            name='paypal_email',
        ),
    ]
