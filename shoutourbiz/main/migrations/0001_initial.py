# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(unique=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='date joined')),
                ('paypal_email', models.EmailField(max_length=254, unique=True, null=True)),
            ],
            options={
                'db_table': 'auth_user',
            },
        ),
        migrations.CreateModel(
            name='BuyerCredits',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('buyer_id', models.IntegerField(max_length=11, db_column='buyer_id')),
                ('buyer_credits', models.CharField(max_length=255, db_column='buyer_credits')),
            ],
            options={
                'db_table': 'buyer_credits',
                'verbose_name_plural': 'BuyerCredits',
            },
        ),
        migrations.CreateModel(
            name='BuyerInfo',
            fields=[
                ('bid', models.AutoField(serialize=False, primary_key=True, db_column='BID')),
                ('email', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=30)),
                ('address', models.TextField()),
            ],
            options={
                'db_table': 'buyer_info',
                'verbose_name_plural': 'BuyerInfo',
            },
        ),
        migrations.CreateModel(
            name='IgClientUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('client', models.CharField(max_length=254)),
                ('username', models.CharField(max_length=30)),
            ],
            options={
                'db_table': 'ig_client_user',
            },
        ),
        migrations.CreateModel(
            name='IgFollower',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=30)),
                ('retrieved', models.IntegerField(default=0)),
                ('analyzed', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'ig_follower',
                'verbose_name_plural': 'IgFollowers',
            },
        ),
        migrations.CreateModel(
            name='IgFollowerTrend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_followers', models.IntegerField()),
                ('date', models.DateField(auto_now_add=True, null=True)),
            ],
            options={
                'db_table': 'ig_follower_trend',
                'verbose_name_plural': 'IgFollowerTrends',
            },
        ),
        migrations.CreateModel(
            name='IgHashtagRanges',
            fields=[
                ('hashtag', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('firstid', models.CharField(max_length=20, db_column='firstID')),
                ('lastid', models.CharField(max_length=20, db_column='lastID')),
            ],
            options={
                'db_table': 'ig_hashtag_ranges',
                'verbose_name_plural': 'IgHashtagRanges',
            },
        ),
        migrations.CreateModel(
            name='IgHashtags',
            fields=[
                ('hashtag', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('last_img_id', models.CharField(max_length=20)),
                ('added', models.DateTimeField()),
            ],
            options={
                'db_table': 'ig_hashtags',
                'verbose_name_plural': 'IgHashtags',
            },
        ),
        migrations.CreateModel(
            name='IgHashtagsLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hashtag1', models.CharField(max_length=100)),
                ('hashtag2', models.CharField(max_length=100)),
                ('frequency', models.IntegerField()),
            ],
            options={
                'db_table': 'ig_hashtags_link',
                'verbose_name_plural': 'IgHashtagsLink',
            },
        ),
        migrations.CreateModel(
            name='IgUsers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=30)),
                ('email', models.CharField(max_length=255)),
                ('followers', models.IntegerField()),
                ('emailscraped', models.DateField(db_column='emailScraped')),
                ('postcount', models.IntegerField(db_column='postCount')),
                ('postavglike', models.IntegerField(db_column='postAvgLike')),
                ('verified', models.IntegerField()),
                ('userid', models.CharField(max_length=30, db_column='userID')),
                ('emailsent', models.IntegerField(db_column='emailSent')),
                ('related_accs_scraped', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False, help_text='Keeps track of whether this account has been deleted on Instagram')),
            ],
            options={
                'db_table': 'ig_users',
                'verbose_name_plural': 'IgUsers',
            },
        ),
        migrations.CreateModel(
            name='IgUsersSocialAccounts',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ig_userid', models.IntegerField(max_length=11, db_column='ig_userid')),
                ('tw_username', models.CharField(max_length=255, null=True, db_column='tw_username')),
                ('fb_username', models.CharField(max_length=255, null=True, db_column='fb_username')),
                ('yt_username', models.CharField(max_length=255, null=True, db_column='yt_username')),
                ('fullname', models.CharField(max_length=255, null=True, db_column='fullname')),
            ],
            options={
                'db_table': 'ig_users_social_accounts',
                'verbose_name_plural': 'IgUsersSocialAccounts',
            },
        ),
        migrations.CreateModel(
            name='IgUserTags',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('userid', models.CharField(max_length=11, db_column='userID')),
                ('hashtag', models.CharField(max_length=100)),
                ('frequency', models.IntegerField()),
                ('iguser', models.ForeignKey(to='main.IgUsers', null=True)),
            ],
            options={
                'db_table': 'ig_user_tags',
                'verbose_name_plural': 'IgUserTags',
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('iid', models.AutoField(serialize=False, primary_key=True, db_column='IID')),
                ('budget', models.IntegerField(null=True, blank=True)),
                ('price', models.IntegerField()),
                ('date', models.DateField()),
                ('bid', models.ForeignKey(to='main.BuyerInfo', db_column='BID')),
            ],
            options={
                'db_table': 'invoice',
                'verbose_name_plural': 'Invoice',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.CharField(max_length=254, null=True, blank=True)),
                ('timestamp', models.CharField(max_length=254)),
                ('receipt', models.CharField(max_length=254)),
                ('amount', models.CharField(max_length=12)),
                ('customer_name', models.CharField(max_length=254, null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('recur', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('started', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('receipt', models.CharField(max_length=255)),
                ('disabled', models.BooleanField(default=False)),
                ('month_uses', models.IntegerField(default=300)),
                ('payment_period', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='TwKeywords',
            fields=[
                ('keyword', models.CharField(max_length=31, serialize=False, primary_key=True)),
                ('last_update', models.DateField(null=True, blank=True)),
                ('added', models.DateTimeField()),
            ],
            options={
                'db_table': 'tw_keywords',
                'verbose_name_plural': 'TwKeywords',
            },
        ),
        migrations.CreateModel(
            name='TwUserKeywords',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('keyword', models.CharField(max_length=31)),
                ('userid', models.CharField(max_length=11, db_column='userID')),
            ],
            options={
                'db_table': 'tw_user_keywords',
                'verbose_name_plural': 'TwUserKeywords',
            },
        ),
        migrations.CreateModel(
            name='TwUsers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=31, db_column='screenName')),
                ('name', models.CharField(max_length=63)),
                ('email', models.CharField(max_length=255)),
                ('emailscraped', models.DateField(db_column='emailScraped')),
                ('followers', models.IntegerField(db_column='followersCount')),
                ('statusescount', models.IntegerField(db_column='statusesCount')),
                ('verified', models.IntegerField()),
                ('avgretweet', models.IntegerField(db_column='avgRetweet')),
                ('avgfav', models.IntegerField(db_column='avgFav')),
                ('emailsent', models.IntegerField(db_column='emailSent')),
                ('userid', models.CharField(max_length=30, db_column='userID')),
            ],
            options={
                'db_table': 'tw_users',
                'verbose_name_plural': 'TwUsers',
            },
        ),
        migrations.CreateModel(
            name='UnlockedUsers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('buyer_id', models.IntegerField(max_length=11, db_column='buyer_id')),
                ('user_id', models.IntegerField(max_length=11, db_column='user_id')),
                ('network', models.CharField(max_length=255, db_column='network')),
            ],
            options={
                'db_table': 'unlocked_users',
                'verbose_name_plural': 'UnlockedUsers',
            },
        ),
        migrations.CreateModel(
            name='VerifiedUserAccounts',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.CharField(max_length=254)),
                ('network', models.CharField(max_length=5)),
                ('account_id', models.CharField(max_length=30, null=True, blank=True)),
                ('price', models.DecimalField(max_digits=12, decimal_places=2)),
                ('note', models.TextField(max_length=1000, null=True, blank=True)),
                ('cpm', models.FloatField(null=True)),
            ],
            options={
                'db_table': 'verified_user_accounts',
                'verbose_name_plural': 'VerifiedUserAccounts',
            },
        ),
        migrations.CreateModel(
            name='VerifiedUserNiches',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('niche', models.CharField(max_length=254)),
                ('network', models.CharField(max_length=5)),
                ('verified_accounts', models.ManyToManyField(related_name='niches', to='main.VerifiedUserAccounts')),
            ],
            options={
                'db_table': 'verified_user_niches',
                'verbose_name_plural': 'VerifiedUserNiches',
            },
        ),
        migrations.CreateModel(
            name='BuyerUses',
            fields=[
                ('uid', models.ForeignKey(primary_key=True, db_column='uid', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('uses', models.IntegerField()),
            ],
            options={
                'db_table': 'buyer_uses',
                'verbose_name_plural': 'BuyerUses',
            },
        ),
        migrations.AddField(
            model_name='verifieduseraccounts',
            name='users_opened',
            field=models.ManyToManyField(related_name='opened_accounts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='twusers',
            name='verified_acc',
            field=models.OneToOneField(related_name='tw_user', null=True, to='main.VerifiedUserAccounts'),
        ),
        migrations.AddField(
            model_name='twuserkeywords',
            name='twuser',
            field=models.ForeignKey(to='main.TwUsers', null=True),
        ),
        migrations.AddField(
            model_name='subscriptiondata',
            name='user',
            field=models.OneToOneField(related_name='subscription', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='igusers',
            name='verified_acc',
            field=models.OneToOneField(related_name='ig_user', null=True, to='main.VerifiedUserAccounts'),
        ),
        migrations.AddField(
            model_name='igfollowertrend',
            name='ig_user',
            field=models.ForeignKey(to='main.IgUsers'),
        ),
        migrations.AddField(
            model_name='igfollower',
            name='following',
            field=models.ForeignKey(to='main.IgUsers'),
        ),
        migrations.AddField(
            model_name='authuser',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='authuser',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
        migrations.AlterUniqueTogether(
            name='verifieduserniches',
            unique_together=set([('niche', 'network')]),
        ),
        migrations.AlterUniqueTogether(
            name='verifieduseraccounts',
            unique_together=set([('network', 'account_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='twuserkeywords',
            unique_together=set([('userid', 'keyword')]),
        ),
    ]
