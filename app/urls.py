from django.urls import path
from . import views

app_name = 'form_app'

urlpatterns = [
    path('', views.login, name='login'),
    path('register/', views.register, name='register'),
]