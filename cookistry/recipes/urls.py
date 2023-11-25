'''
Mapping the url requrest

This file maps the url requrest from member app and share it with recipes.url
'''

from django.urls import path
from . import views

urlpatterns = [
    path('', views.recipes, name='index'),
    path('new',views.new_recipe, name='add_recipe'),
    path('<int:pk>',views.get_recipe, name='get_recipe'),
    path('<int:pk>/edit',views.edit_recipe,name='edit_recipe'),
    path('<int:pk>/add_review',views.add_review,name='add_review'),
    path('<int:recipe_id>/procedure/<int:order>',views.get_procedure,name='get_procedure'),
    # delete review in user settings
    path('<int:pk>/delete',views.delete_recipe,name='delete_recipe'),
    path('search',views.search_recipe,name='search')
]