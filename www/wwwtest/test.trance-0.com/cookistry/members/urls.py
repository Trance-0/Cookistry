"""
Mapping the url requrest

This file maps the url requrest from member app and share it with cookistry.url
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.members, name='members'),
    path('login/',views.login_request,name='login'),
    path('register/',views.register_request,name='register'),
    path('profile/<str:username>',views.get_profile,name='profile'),
    path('profile/<str:username>/edit',views.edit_profile,name='edit_profile'),
    path('profile/<str:username>/edit_reviews',views.edit_reviews,name='edit_reviews'),
    path('logout/',views.logout_request,name="logout")
]