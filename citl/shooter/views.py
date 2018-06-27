# https://docs.djangoproject.com/en/2.0/intro/tutorial01/

import datetime

from collections import Counter

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect
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
	
		weekRange = range(1,16)

		scores = Score.objects \
				.values('shooter__first_name', 'shooter__last_name', 'week', 'bunker_one', 'bunker_two', 'average', \
					'team__captain__first_name', 'team__captain__last_name' ) \
				.filter(team__season=year, team__team_name=team) \
				.order_by('shooter__first_name', 'week')
				
		scorecard = {}
		for score in scores:
			personName = score['shooter__first_name'] + " " + score['shooter__last_name']
			if personName not in scorecard:
				scorecard[personName] = { 'weeks': dict.fromkeys(weekRange,'-'), 'count': 0, 'average': score['average'] }
			
			scorecard[personName]['weeks'][score['week']] = score['bunker_one'] + score['bunker_two']
			scorecard[personName]['count'] += 1
		
		context = {
			'scores': scorecard,
			'team': team,
			'weekRange': weekRange,
			'season': year,
		}
		
		return render(request, 'shooter/scorecard.html', context)
		
#TODO: class StandingsView(View):
		
class AdministrationView(UserPassesTestMixin, View):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()
		
	def get(self, request):
	
		context = {
			'test': "Hello World",
		}
		
		return render(request, 'shooter/administration.html', context)
	
# TODO: Get UserPassesTest involved here. Turn this into a class if possible, for consistency
from django.views.generic.edit import FormView
from .forms import TeamForm

class TeamFormView(UserPassesTestMixin, FormView):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()

	template_name = 'shooter/newteam.html'
	form_class = TeamForm
	success_url = '/shooter/administration/newteam/'
	
	def get_context_data(self, **kwargs):	# provides context for form_invalid by overriding the default get_context_data method
	
		test = "Hello World"
	
		if 'context_key' not in kwargs:  # set value if not present
			kwargs['test'] = test
			
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
	
		response = super().form_valid(form)
		
		c_team_name = form.cleaned_data['team_name']
		c_season	= form.cleaned_data['season']
		message		= c_team_name + " successfully added to " + str(c_season) + " season"
	
		new_team = Team(team_name=c_team_name, season=c_season)
		new_team.save()
		
		messages.add_message(self.request, messages.INFO, message)
		
		return response
		
	def form_invalid(self, form):
	
		response = super().form_invalid(form)
		
		form = TeamForm()
		
		return response
		
#class ShooterFormView(UserPassesTestMixin, FormView):

#	def test_func(self):
#		return self.request.user.groups.filter(name='League Administrators').exists()

"""
def get_team(request):
	if request.method == 'POST':
		form = TeamForm(request.POST)

		if form.is_valid():
			new_team = Team(team_name=form.cleaned_data['team_name'], season=form.cleaned_data['season'])
			new_team.save()
			
			return HttpResponseRedirect('/shooter/administration/', {'message': "Team Saved"})

	else:
		form = TeamForm()
		
	context = {
		'form': form,
	}

	return render(request, 'shooter/team.html', context)
"""