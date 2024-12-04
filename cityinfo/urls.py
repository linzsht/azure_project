from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_city_details, name='get_city_details'),
]
