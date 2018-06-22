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
	
class SeasonView(View):	
	def get(self, request, year):
	
		season = Team.objects.values('season', 'team_name').filter(season=year).distinct()

		context = {
			'season': season,
			'year': year,
		}
		
		return render(request, 'shooter/season.html', context)

class ScorecardView(View):
	
	def get(self, request, year, team):
	
		persons = set()

		scores = Score.objects \
				.values('shooter__first_name', 'team__season', 'team__captain__first_name', 'week', 'bunker_one', 'bunker_two') \
				.filter(team__season=year, team__team_name=team) \
				.order_by('shooter__first_name', 'week')
				
		scorecard = {}
		
		for score in scores:
			personName = score['shooter__first_name']
			if personName not in scorecard:
				scorecard[personName] = { 'weeks': [] }
			
			scorecard[personName]['weeks'].append({
				score['week']: score['bunker_one'] + score['bunker_two']
			})
			
		
		for person in Score.objects.all().select_related().filter(team__season=year, team__team_name=team):
			persons.add(person)
		
		context = {
			'scores': scorecard,
			'persons': persons,
			'team': team,
			'range': range(1,16),
			'season': year,
		}
		
		
		# In this example, j is the object Shooter filtered based on name being Joe.
		#j = Shooter.objects.get(first_name="Joe")
		#joe = j.first_name
		
		# In this example I go straight for what I want out of the Shooter object, filtering on Jane
		#jane = Shooter.objects.get(first_name="Jane").first_name
		
		return render(request, 'shooter/scorecard.html', context)
		
class ScoreEntry(UserPassesTestMixin, View):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()
		
	def get(self, request, year):
	
		context = {
			'test': "Hello World",
		}
		
		return render(request, 'shooter/scoreentry.html', context)