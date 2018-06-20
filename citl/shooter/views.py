# https://docs.djangoproject.com/en/2.0/intro/tutorial01/

import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render
from django.views import View
from django.core import serializers

from .models import Shooter, Team, Score

	
class IndexView(View):	
	def get(self, request):
	
		all_season = Team.objects.values('season', 'team_name').order_by('-season').distinct()
		
		now = datetime.datetime.now()
	
		context = {
			'all_season': all_season,
			'current_year': now.year,
		}		

		return render(request, 'shooter/index.html', context)
		
		
		#season = Season.objects.values('season_year','team__team_name').order_by('season_year').distinct()	
	
		# In this example, j is the object Shooter filtered based on name being Joe.
		#j = Shooter.objects.get(first_name="Joe")
		#joe = j.first_name
		
		# In this example I go straight for what I want out of the Shooter object, filtering on Jane
		#jane = Shooter.objects.get(first_name="Jane").first_name
		
	#def post
	#def put
	#def delete
	
class SeasonView(View):	
	def get(self, request, year):
	
		season = Team.objects.values('season', 'team_name').filter(season=year).distinct()

		context = {
			'season': season,
			'year': year,
		}
		
		return render(request, 'shooter/season.html', context)

class TeamView(UserPassesTestMixin, View):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()
	
	def get(self, request, year, team):
	
		team = Score.objects.values('team__season', 'team__team_name', 'shooter__first_name', 'shooter__last_name', 'average').filter(team__season=year, team__team_name=team)
		
		context = {
			'team': team,
		}
		
		return render(request, 'shooter/team.html', context)