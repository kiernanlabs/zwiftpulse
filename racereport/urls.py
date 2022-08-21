from django.urls import path

from . import views

urlpatterns = [
    path('', views.RaceCatView.as_view(), name='race-cats'),
]