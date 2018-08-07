from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import ugettext_lazy as _
from datetime import datetime
from .utils_helper import dt_to_aware

from django.contrib.auth.models import AbstractUser

from main.utils_helper import calculate_engagement_stats_2, calculate_engagement_stats_for_verified_users, \
    calculate_cpm_before_save

class BuyerInfo(models.Model):
    bid = models.AutoField(db_column='BID', primary_key=True)  # Field name made lowercase.
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    address = models.TextField()

    class Meta:
        db_table = 'buyer_info'
        verbose_name_plural = 'BuyerInfo'

class Invoice(models.Model):
    iid = models.AutoField(db_column='IID', primary_key=True)  # Field name made lowercase.
    bid = models.ForeignKey(BuyerInfo, db_column='BID')  # Field name made lowercase.
    budget = models.IntegerField(blank=True, null=True)
    price = models.IntegerField()
    date = models.DateField()

    class Meta:
        db_table = 'invoice'
        verbose_name_plural = 'Invoice'


class AuthUserManager(BaseUserManager):
    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)

class AuthUser(AbstractBaseUser, PermissionsMixin):
    """
    Used for all authenticated user (influencers, brands, assistants, superuser, etc...)
    """

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), max_length=254, unique=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    objects = AuthUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.email

    def is_buyer(self):
        return self.groups.filter(name='buyer').exists()

    def is_month_buyer(self):
        return self.groups.filter(name='month_buyer').exists()

    class Meta:
        db_table = 'auth_user'


class BuyerUses(models.Model):
    uid = models.ForeignKey(AuthUser, db_column='uid', primary_key=True)
    uses = models.IntegerField()

    class Meta:
        db_table = 'buyer_uses'
        verbose_name_plural = 'BuyerUses'

    def __unicode__(self):
        return str(self.uses)


class SubscriptionData(models.Model):
    user = models.OneToOneField(AuthUser, related_name='subscription')
    started = models.DateTimeField()
    end = models.DateTimeField()
    receipt = models.CharField(max_length=255)
    disabled = models.BooleanField(default=False)
    month_uses = models.IntegerField(default=300)
    payment_period = models.IntegerField(default=1)

    def check_active(self):
        now = dt_to_aware(datetime.now())
        if not self.disabled and self.end >= now:
            return True

    def __unicode__(self):
        return self.receipt

class Payment(models.Model):
    email = models.CharField(max_length=254, blank=True, null=True)
    timestamp = models.CharField(max_length=254)
    receipt = models.CharField(max_length=254)
    amount = models.CharField(max_length=12)
    customer_name = models.CharField(max_length=254, blank=True, null=True)
    active = models.BooleanField(default=True)
    recur = models.BooleanField(default=False)

    def __unicode__(self):
        return self.email


class IgClientUser(models.Model):
    client = models.CharField(max_length=254)
    username = models.CharField(max_length=30)

    class Meta:
        db_table = 'ig_client_user'


class IgHashtagRanges(models.Model):
    """
    Used in old API-based scraping script. Stores the
    hashtag, and the id of the first post and the id of
    the last post to scrape.
    """
    hashtag = models.CharField(primary_key=True, max_length=100)
    firstid = models.CharField(db_column='firstID', max_length=20)  # Field name made lowercase.
    lastid = models.CharField(db_column='lastID', max_length=20)  # Field name made lowercase.

    class Meta:
        db_table = 'ig_hashtag_ranges'
        verbose_name_plural = 'IgHashtagRanges'


class IgHashtags(models.Model):
    """
    Stores all IG niches.
    """
    hashtag = models.CharField(primary_key=True, max_length=100)
    last_img_id = models.CharField(max_length=20)
    added = models.DateTimeField()

    class Meta:
        db_table = 'ig_hashtags'
        verbose_name_plural = 'IgHashtags'


class IgHashtagsLink(models.Model):
    hashtag1 = models.CharField(max_length=100)
    hashtag2 = models.CharField(max_length=100)
    frequency = models.IntegerField()

    class Meta:
        db_table = 'ig_hashtags_link'
        verbose_name_plural = 'IgHashtagsLink'


class VerifiedUserAccounts(models.Model):
    """
    Stores confirmed ("verified") users. Confirmed users
    have their own niches, which is located in VerifiedUserNiches.

    They also have a price, which is the amount they want to sell their
    contact info. The price is set when they sign up for the website as 
    a publisher.

    The CPM is calculated for each verified user in the script "calculate_ig_cpm" 
    and "calculate_tw_cpm"
    """
    email = models.CharField(max_length=254)
    network = models.CharField(max_length=5)
    account_id = models.CharField(max_length=30, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.TextField(max_length=1000, blank=True, null=True)
    users_opened = models.ManyToManyField(AuthUser, related_name='opened_accounts')
    cpm = models.FloatField(null=True)

    def save(self, *args, **kwargs):
        self.cpm = calculate_cpm_before_save(self)
        super(VerifiedUserAccounts, self).save(*args, **kwargs)

    class Meta:
        db_table = 'verified_user_accounts'
        unique_together = (('network', 'account_id'),)
        verbose_name_plural = 'VerifiedUserAccounts'

class IgUsers(models.Model):
    """
    Stores information relevant to IG users
    """
    username = models.CharField(unique=True, max_length=30)
    email = models.CharField(max_length=255)
    followers = models.IntegerField()
    emailscraped = models.DateField(db_column='emailScraped')  # Field name made lowercase.
    postcount = models.IntegerField(db_column='postCount')  # Field name made lowercase.
    postavglike = models.IntegerField(db_column='postAvgLike')  # Field name made lowercase.
    verified = models.IntegerField()
    userid = models.CharField(db_column='userID', max_length=30)  # Field name made lowercase.
    emailsent = models.IntegerField(db_column='emailSent')  # Field name made lowercase.
    verified_acc = models.OneToOneField(VerifiedUserAccounts, null=True,
                                        related_name='ig_user', on_delete=models.CASCADE)
    related_accs_scraped = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False, help_text='Keeps track of whether this account has been deleted on Instagram')
    engagement = models.FloatField()

    def save(self, *args, **kwargs):
        # update engagement stats
        self.engagement = calculate_engagement_stats_2(self)
        # update verified account info by activating the save() method (for elasticsearch)
        verified_acc = VerifiedUserAccounts.objects.filter(account_id=self.id, network='ig')
        if verified_acc.exists():
            verified_acc.first().save()

        super(IgUsers, self).save(*args, **kwargs)

    class Meta:
        db_table = 'ig_users'
        verbose_name_plural = 'IgUsers'

class IgUserTags(models.Model):
    """
    Stores hashtags for all (confirmed & unconfirmed) IG users.
    """
    iguser = models.ForeignKey(IgUsers, on_delete=models.CASCADE, null=True)
    userid = models.CharField(db_column='userID', max_length=11)  # Field name made lowercase.
    hashtag = models.CharField(max_length=100)
    frequency = models.IntegerField()

    class Meta:
        db_table = 'ig_user_tags'
        verbose_name_plural = 'IgUserTags'

class IgFollower(models.Model):
    """
    Stores followers for all (confirmed & unconfirmed) IG users.
    """
    username = models.CharField(max_length=30)
    following = models.ForeignKey(IgUsers, on_delete=models.CASCADE)
    retrieved = models.IntegerField(default=0)
    analyzed = models.IntegerField(default=0)

    class Meta:
        db_table = 'ig_follower'
        verbose_name_plural = 'IgFollowers'

class IgFollowerTrend(models.Model):
    """
    Stores the number of followers for all IG users
    as a function of time.
    """
    ig_user = models.ForeignKey(IgUsers, on_delete=models.CASCADE)
    num_followers = models.IntegerField()
    date = models.DateField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'ig_follower_trend'
        verbose_name_plural = 'IgFollowerTrends'

class TwKeywords(models.Model):
    """
    Stores all TW niches.
    """
    keyword = models.CharField(primary_key=True, max_length=31)
    last_update = models.DateField(blank=True, null=True)
    added = models.DateTimeField()

    class Meta:
        db_table = 'tw_keywords'
        verbose_name_plural = 'TwKeywords'

class TwUsers(models.Model):
    """
    Stores all TW users.
    """
    username = models.CharField(db_column='screenName', unique=True, max_length=31)  # Field name made lowercase.
    name = models.CharField(max_length=63)
    email = models.CharField(max_length=255)
    emailscraped = models.DateField(db_column='emailScraped')  # Field name made lowercase.
    followers = models.IntegerField(db_column='followersCount')  # Field name made lowercase.
    statusescount = models.IntegerField(db_column='statusesCount')  # Field name made lowercase.
    verified = models.IntegerField()
    avgretweet = models.IntegerField(db_column='avgRetweet')  # Field name made lowercase.
    avgfav = models.IntegerField(db_column='avgFav')  # Field name made lowercase.
    emailsent = models.IntegerField(db_column='emailSent')  # Field name made lowercase.
    userid = models.CharField(db_column='userID', max_length=30)  # Field name made lowercase.
    verified_acc = models.OneToOneField(VerifiedUserAccounts, null=True,
                                        related_name='tw_user', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # update verified account info by activating the save() method (for elasticsearch)
        verified_acc = VerifiedUserAccounts.objects.filter(account_id=self.id, network='tw')
        if verified_acc.exists():
            verified_acc.first().save()

        super(TwUsers, self).save(*args, **kwargs)

    class Meta:
        db_table = 'tw_users'
        verbose_name_plural = 'TwUsers'

class TwUserKeywords(models.Model):
    """
    Stores niches for all TW users.
    """
    twuser = models.ForeignKey(TwUsers, on_delete=models.CASCADE, null=True)
    keyword = models.CharField(max_length=31)
    userid = models.CharField(db_column='userID', max_length=11)  # Field name made lowercase.

    class Meta:
        db_table = 'tw_user_keywords'
        unique_together = (('userid', 'keyword'),)
        verbose_name_plural = 'TwUserKeywords'

class VerifiedUserNiches(models.Model):
    """
    Stores niches for all verified users.
    """
    verified_accounts = models.ManyToManyField(VerifiedUserAccounts, related_name='niches')
    niche = models.CharField(max_length=254)
    network = models.CharField(max_length=5)

    class Meta:
        db_table = 'verified_user_niches'
        unique_together = (('niche', 'network'),)
        verbose_name_plural = 'VerifiedUserNiches'

class IgUsersSocialAccounts(models.Model):
    ig_userid = models.IntegerField(max_length=11, db_column="ig_userid")
    tw_username = models.CharField(max_length=255, null=True, db_column="tw_username")
    fb_username = models.CharField(max_length=255, null=True, db_column="fb_username")
    yt_username = models.CharField(max_length=255, null=True, db_column="yt_username")
    fullname = models.CharField(max_length=255, null=True, db_column="fullname")
    class Meta:
        db_table = 'ig_users_social_accounts'
        verbose_name_plural = 'IgUsersSocialAccounts'

class BuyerCredits(models.Model):
    buyer_id = models.IntegerField(max_length=11, db_column="buyer_id")
    buyer_credits = models.CharField(max_length=255, db_column="buyer_credits")

    def buyer_email(self):
        buyer = AuthUser.objects.filter(id=self.buyer_id)
        if buyer.exists():
            return buyer.first().email
        else:
            return None

    class Meta:
        db_table = 'buyer_credits'
        verbose_name_plural = 'BuyerCredits'

class UnlockedUsers(models.Model):
    buyer_id = models.IntegerField(max_length=11, db_column="buyer_id")
    user_id = models.IntegerField(max_length=11, db_column="user_id")
    network = models.CharField(max_length=255, db_column="network")

    def buyer_email(self):
        buyer = AuthUser.objects.filter(id=self.buyer_id)
        if buyer.exists():
            return buyer.first().email
        else:
            return None
            
    class Meta:
        db_table = 'unlocked_users'
        verbose_name_plural = 'UnlockedUsers'