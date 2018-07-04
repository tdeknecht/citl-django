# shooter/urls.py

from django.urls import path

from . import views

app_name = 'shooter'

urlpatterns = [
	path('', views.SeasonsView.as_view(), name='seasons'),						# /shooter/
	path('<int:year>/season/', views.SeasonView.as_view(), name='season'),		# /shooter/<year>/season
	path('<int:year>/<team>/scorecard/', views.ScorecardView.as_view(), name='scorecard'),	# /shooter/<year>/<team>/team
	path('administration/', views.AdministrationView.as_view(), name='administration'),		# /shooter/administration
	path('administration/newseason/', views.SeasonFormView.as_view(), name='newteam'),		# /shooter/administration/newteam
	path('administration/newshooter/', views.ShooterFormView.as_view(), name='newshooter'),
	path('administration/newscore/', views.ScoreFormView.as_view(), name='newscore'),
	#path('administration/<team>/newscore/', views.ScoreFormView2.as_view(), name='newscore'),
]