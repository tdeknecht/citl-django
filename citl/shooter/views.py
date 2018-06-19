# https://docs.djangoproject.com/en/2.0/intro/tutorial01/

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render
from django.views import View
from django.core import serializers

from .models import Shooter, Season, Team, Score

	
class IndexView(View):	
	def get(self, request):
	
		all_season = Season.objects.values('season_year','team__team_name').order_by('-season_year').distinct()			
	
		context = {
			'all_season': all_season,
		}		

		return render(request, 'shooter/index.html', context)
		
	#def post
	#def put
	#def delete
	
class SeasonView(View):	
	def get(self, request, year):
	
		season = Season.objects.values('season_year', 'team__team_name').filter(season_year=year).distinct()

		context = {
			'season': season,
		}
		
		return render(request, 'shooter/season.html', context)

class TeamView(UserPassesTestMixin, View):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()
	
	def get(self, request, year, team):
	
		team = Season.objects.values('season_year', 'team__team_name', 'shooter__first_name', 'shooter__last_name', 'shooter__average').filter(season_year=year, team__team_name=team)
		
		context = {
			'team': team,
		}
		
		return render(request, 'shooter/team.html', context)
		
class TestView(View):
	def get(self, request):
	
		# GOAL: List all the teams for this season (2018), their members, and their current averages. GROUPED BY YEAR
		season = Season.objects.values('season_year','team__team_name').order_by('season_year').distinct()	
	
		# In this example, j is the object Shooter filtered based on name being Joe.
		j = Shooter.objects.get(first_name="Joe")
		joe = j.first_name
		
		# In this example I go straight for what I want out of the Shooter object, filtering on Jane
		jane = Shooter.objects.get(first_name="Jane").first_name
	
		context = {
			'season': season,
			'joe': joe,
			'jane': jane,
		}		

		return render(request, 'shooter/test.html', context)
		
	#def post
	#def put
	#def delete