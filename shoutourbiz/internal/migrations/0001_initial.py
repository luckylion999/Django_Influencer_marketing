# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IgFollowerRating',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('age_group', models.CharField(max_length=10, choices=[(b'U', b'Unknown'), (b'0-17', b'0-17'), (b'18-24', b'18-24'), (b'25-34', b'25-34'), (b'35-44', b'35-44'), (b'45-54', b'45-54'), (b'55+', b'55+')])),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2)),
                ('gender', models.CharField(max_length=10, choices=[(b'U', b'Unknown'), (b'M', b'Male'), (b'F', b'Female')])),
                ('date_created', models.DateField(auto_now_add=True, null=True)),
                ('assistant', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
                ('ig_follower', models.ForeignKey(to='main.IgFollower', null=True)),
            ],
            options={
                'db_table': 'ig_follower_rating',
            },
        ),
    ]
