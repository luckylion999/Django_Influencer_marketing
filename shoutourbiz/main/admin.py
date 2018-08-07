from django.contrib import admin
from . import models
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext as _
from .forms import RegistrationForm
from django.conf import settings
from django import forms
from .models import AuthUser

class UserChangeForm(forms.ModelForm):
    """
    A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = AuthUser
        fields = ('email', 'password', 'first_name', 'last_name', 'is_active', 
            'is_superuser', 'groups', 'user_permissions')

    def clean_password(self):
        return self.initial["password"]

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = RegistrationForm
    list_display = ('email', 'first_name', 'last_name', 'is_superuser', 'date_joined', 'group')
    list_filter = BaseUserAdmin.list_filter
    fieldsets = (
        (None, {'fields': ('email', 'password', 'is_active')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'last_login')
        }),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    def group(self, obj):
        if not obj:
            return None
        groups = obj.groups.values_list('name', flat=True)
        if len(groups) <= 0:
            return None
        return groups[0].encode('utf-8')

class IgUsersAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'userid']
    search_fields = ['id', 'username', 'email']
class BuyerInfoAdmin(admin.ModelAdmin):
    list_display = ['bid', 'email', 'phone', 'address']
    search_fields = ['id', 'bid', 'email', 'phone']  
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['iid', 'bid', 'budget', 'price', 'date'] 
    search_fields = ['id', 'iid', 'bid', 'budget', 'price', 'date'] 
class BuyerUsersAdmin(admin.ModelAdmin):
    list_display = ['uid', 'uses'] 
class IgHashtagRangesAdmin(admin.ModelAdmin):
    list_display = ['hashtag', 'firstid', 'lastid']
class IgHashtagsAdmin(admin.ModelAdmin):
    list_display = ['hashtag', 'last_img_id', 'added']
    search_fields = ['id', 'hashtag', 'added']
class IgHashtagsLinkAdmin(admin.ModelAdmin):
    list_display = ['hashtag1', 'hashtag2', 'frequency']
class IgUserTagsAdmin(admin.ModelAdmin):
    list_display = ['iguser', 'userid', 'hashtag', 'frequency']
    search_fields = ['id', 'iguser', 'userid', 'hashtag']
class TwKeywordsAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'last_update', 'added']
    search_fields = ['id', 'keyword', 'added']
class TwUserKeywordsAdmmin(admin.ModelAdmin):
    list_display = ['twuser', 'keyword', 'userid']
    search_fields = ['id', 'twuser', 'keyword']
class TwUsersAdmin(admin.ModelAdmin):
    list_display = ['username', 'name', 'email', 'emailscraped',
        'followers', 'statusescount', 'verified', 'avgretweet', 'avgfav',
        'emailsent', 'userid', 'verified_acc']
    search_fields = ['id', 'username', 'name', 'email', 'followers', 'userid']
class VerifiedUserAccountsAdmin(admin.ModelAdmin):
    list_display = ['email', 'network', 'price', 'cpm']
    search_fields = ['id', 'email', 'network']
class IgFollowerAdmin(admin.ModelAdmin):
    list_display = ['username', 'following']
    search_fields = ['id', 'username', 'following']
class BuyerCreditsAdmin(admin.ModelAdmin):
    list_display = ['buyer_email','buyer_id', 'buyer_credits']
class UnlockedUsersAdmin(admin.ModelAdmin):
    list_display = ['buyer_id', 'buyer_email', 'user_id', 'network']

admin.site.register(models.AuthUser, UserAdmin)
admin.site.register(models.BuyerInfo, BuyerInfoAdmin)
admin.site.register(models.Invoice, InvoiceAdmin)
admin.site.register(models.BuyerUses, BuyerUsersAdmin)
admin.site.register(models.IgHashtagRanges, IgHashtagRangesAdmin)
admin.site.register(models.IgHashtags, IgHashtagsAdmin)
admin.site.register(models.IgHashtagsLink, IgHashtagsLinkAdmin)
admin.site.register(models.IgUserTags, IgUserTagsAdmin)
admin.site.register(models.IgUsers, IgUsersAdmin)
admin.site.register(models.TwKeywords, TwKeywordsAdmin)
admin.site.register(models.TwUserKeywords, TwUserKeywordsAdmmin)
admin.site.register(models.TwUsers, TwUsersAdmin)
admin.site.register(models.VerifiedUserAccounts, VerifiedUserAccountsAdmin)
admin.site.register(models.IgFollower, IgFollowerAdmin)
admin.site.register(models.BuyerCredits, BuyerCreditsAdmin)
admin.site.register(models.UnlockedUsers, UnlockedUsersAdmin)