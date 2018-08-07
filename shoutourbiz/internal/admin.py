from django.contrib import admin

from . import models

class IgFollowerRatingAdmin(admin.ModelAdmin):
    list_display = ['id', 'profile_username', 'assistant_name', 'age_group', 'country', 'gender']
    search_fields = ['assistant__first_name', 'assistant__last_name']
    list_display_links = None

    def profile_username(self, obj):
        if not obj:
            return None
        return '<a href="https://www.instagram.com/{0}/" target="_blank">{1}</a>'.format(obj.ig_follower.username, obj.ig_follower.username)
    profile_username.allow_tags = True

    def assistant_name(self, obj):
    	if not obj:
    		return None
    	return '{0} {1}'.format(obj.assistant.first_name, obj.assistant.last_name)

admin.site.register(models.IgFollowerRating, IgFollowerRatingAdmin)