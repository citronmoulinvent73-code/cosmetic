from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import index
from . import views

urlpatterns = [
    path("", index, name="index"),
    path("top/", views.top, name="top"), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)