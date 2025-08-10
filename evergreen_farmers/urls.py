from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.conf.urls import handler500
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('farmers_website.urls')), 
]

# Serving media & static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'farmers_website.views.custom_404_view'
handler500 = 'farmers_website.views.custom_500_view'

