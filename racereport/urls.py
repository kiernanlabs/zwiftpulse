from django.urls import path

from . import views

urlpatterns = [
    path('', views.this_week, name='this_week'),
    path('today/<str:category>', views.last_24hrs, name='last_24hrs'),
    path('week/', views.this_week, name='this_week'),
    path('week/<str:category>', views.this_week, name='this_week'),
    path('team/<str:team_name>/', views.this_week_team_results, name='team_results'),
    path('team/<str:team_name>/<str:category>', views.this_week_team_results, name='team_results'),
]