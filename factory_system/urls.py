"""
URL configuration for factory_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def quiet_probe_view(request):
    """Quiet handler for browser favicon and devtools requests to avoid 404 console noise."""
    return HttpResponse(status=204)

urlpatterns = [
    path("favicon.ico", quiet_probe_view, name="favicon"),
    path(".well-known/appspecific/com.chrome.devtools.json", quiet_probe_view),
    path("admin/", admin.site.urls),
    path("", include("operations.urls")),
]

# Serve user-uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

