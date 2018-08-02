# shooter/urls.py

from django.urls import path, re_path

from . import views

app_name = 'shooter'

urlpatterns = [
	path('', views.SeasonsView.as_view(), name='seasons'),						# /shooter/
	path('<int:year>/season/', views.SeasonView.as_view(), name='season'),
	path('<int:year>/<team>/scorecard/', views.ScorecardView.as_view(), name='scorecard'),
	path('administration/', views.AdministrationView.as_view(), name='administration'),
	path('administration/newteam/', views.NewTeamView.as_view(), name='newteam'),
	path('administration/newshooter/', views.NewShooterView.as_view(), name='newshooter'),
	path('administration/<team>/newscore/', views.NewScoreView.as_view(), name='newscore'),
	#path('administration/newscore/', views.NewScoreView.as_view(), name='newscore'),
	path('test/', views.TestView.as_view(), name='test'),
]