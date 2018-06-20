# shooter/urls.py

from django.urls import path

from . import views

app_name = 'shooter'

urlpatterns = [
	path('', views.IndexView.as_view(), name='index'),							# /shooter/
	path('<int:year>/season/', views.SeasonView.as_view(), name='season'),		# /shooter/<year>/season
	path('<int:year>/<team>/scorecard/', views.ScorecardView.as_view(), name='scorecard'),	# /shooter/<year>/<team>/team
]