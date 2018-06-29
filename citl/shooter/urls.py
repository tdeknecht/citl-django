# shooter/urls.py

from django.urls import path

from . import views

app_name = 'shooter'

urlpatterns = [
	path('', views.IndexView.as_view(), name='index'),							# /shooter/
	path('<int:year>/season/', views.SeasonView.as_view(), name='season'),		# /shooter/<year>/season
	path('<int:year>/<team>/scorecard/', views.ScorecardView.as_view(), name='scorecard'),	# /shooter/<year>/<team>/team
	path('administration/', views.AdministrationView.as_view(), name='administration'),		# /shooter/administration
	path('administration/newteam/', views.TeamFormView.as_view(), name='newteam'),
	path('administration/newshooter/', views.ShooterFormView.as_view(), name='newshooter'),
	#path('team/', views.get_team, name='team'),
]