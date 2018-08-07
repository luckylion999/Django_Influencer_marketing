from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from main.views import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views
from django.views import static as static_views
from django.conf.urls.static import static
from main import urls

urlpatterns = [

    url(r'^admin/', include(admin.site.urls)),
    url('^', include(urls, namespace='main'), name='main'),
    url(r'^internal/', include('internal.urls', namespace='internal')),
    url(r'^profiles/', include('profiles.urls', namespace='profiles')),
    url(r"^payments/", include("payments.urls", namespace='payments')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns