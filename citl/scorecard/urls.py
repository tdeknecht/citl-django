# scorecard/urls.py

from django.urls import path

from . import views

# defining an app_name allows me to namespace my URLs between apps. 
# This prevents any conflicts between, say, 'detail' being defined in multiple apps in the same project.

app_name = 'scorecard'

urlpatterns = [
	path('', views.IndexView.as_view(), name='index'),
]