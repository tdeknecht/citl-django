# https://docs.djangoproject.com/en/2.0/intro/tutorial01/

import datetime

from collections import Counter

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from django.views.generic.edit import FormView, CreateView
from django.views import View
from django.http import HttpResponseRedirect
from django.core import serializers
from django.db import IntegrityError, transaction

from .models import Shooter, Team, Score
from .forms import TeamForm, BaseTeamFormSet, ShooterForm, ScoreForm
	
class SeasonsView(View):	
	def get(self, request):
	
		all_season = Team.objects.values('season', 'team_name').order_by('-season').distinct()
		
		now = datetime.datetime.now()
	
		context = {
			'all_season': all_season,
			'current_year': now.year,
		}		

		return render(request, 'shooter/seasons.html', context)
	
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
		
class AdministrationView(UserPassesTestMixin, View):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()
		
	def get(self, request):
	
		now = datetime.datetime.now()
	
		this_season = Team.objects.values('team_name').order_by('team_name').filter(season=now.year)
	
		context = {
			'this_season': this_season,
			'current_year': now.year,
		}	
		
		return render(request, 'shooter/administration.html', context)
		
# FORMS

class TeamFormView(UserPassesTestMixin, FormView):
	"""Form used to submit new Teams
	"""

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()

	template_name = 'shooter/newteam.html'
	form_class = TeamForm
	success_url = '/shooter/administration/newteam/'

	def form_valid(self, form):
	
		response = super().form_valid(form)
		
		c_team_name = form.cleaned_data['team_name']
		c_season	= form.cleaned_data['season']
		c_captain	= form.cleaned_data['captain']

		team_object = Team.objects.filter(first_name=c_team_name, season=c_season).exists()
		
		if team_object:
			message = "ERROR: " + c_team_name + " already exists"
		else:
			new_team 	= Team(team_name = c_team_name,
								season = c_season,
								captain = c_captain
								)
			new_team.save()
			message		= c_team_name + " successfully added"
		
		messages.add_message(self.request, messages.INFO, message)
		
		return response
		
	def form_invalid(self, form):
	
		response = super().form_invalid(form)
		
		form = TeamForm()
		
		return response
		
class ShooterFormView(UserPassesTestMixin, FormView):
	"""Form used to add a new Shooter to the league roster
	"""

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()

	template_name = 'shooter/newshooter.html'
	form_class = ShooterForm
	success_url = '/shooter/administration/newshooter/'
		
	def form_valid(self, form):
	
		response = super().form_valid(form)
		
		c_first_name 	= form.cleaned_data['first_name']
		c_last_name		= form.cleaned_data['last_name']
		c_email			= form.cleaned_data['email']
		c_rookie		= form.cleaned_data['rookie']
		c_guest			= form.cleaned_data['guest']
		
		shooter_object = Shooter.objects.filter(first_name=c_first_name, last_name=c_last_name).exists()
		
		if shooter_object:
			message = "ERROR: " + c_first_name + " " + c_last_name + " already exists"
		else:
			new_shooter 	= Shooter(first_name = c_first_name,
								last_name = c_last_name,
								email = c_email,
								rookie = c_rookie,
								guest = c_guest
								)
			new_shooter.save()
			message		= c_first_name + " " + c_last_name + " successfully added"
		
		messages.add_message(self.request, messages.INFO, message)
		
		return response
		
	def form_invalid(self, form):
	
		response = super().form_invalid(form)
		
		form = ShooterForm()
		
		return response

class ScoreFormView(UserPassesTestMixin, FormView):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()

	template_name = 'shooter/newscore.html'
	form_class = ScoreForm
	success_url = '/shooter/administration/newscore/'
	
	def get_context_data(self, **kwargs):	# provides context for form_invalid by overriding the default get_context_data method
	
		test = "Hello World"
	
		if 'context_key' not in kwargs:  # set value if not present
			kwargs['test'] = test
			
		return super().get_context_data(**kwargs)
		
	def form_valid(self, form):
	
		response = super().form_valid(form)
		
		message = "Temp message"
		
		messages.add_message(self.request, messages.INFO, message)
		
		return response
		
	def form_invalid(self, form):
	
		response = super().form_invalid(form)
		
		form = ScoreForm()
		
		return response

"""
class TeamCreateView(UserPassesTestMixin, CreateView):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()

	now = datetime.datetime.now().year
	
	#form = Team
	model = Team
	fields = ['team_name', 'captain', 'season']
	
	initial = {'season': now}
	template_name = 'shooter/newteam2.html'

	def get_context_data(self, **kwargs):
		context = super(TeamCreateView, self).get_context_data(**kwargs)
		if self.request.POST:
			context['team_form'] = TeamFormSet(self.request.POST)
		else:
			context['team_form'] = TeamFormSet()
		return context
		
	def form_valid(self, form):
		context = self.get_context_data()
		team_form = context['team_formset']
		if team_form.is_valid():
			c_team_name = form.cleaned_data['team_name']
			c_season	= form.cleaned_data['season']
			c_captain	= form.cleaned_data['captain']

			team_object = Team.objects.filter(team_name=c_team_name, season=c_season).exists()
			
			if team_object:
				message = "ERROR: " + c_team_name + " already exists"
			else:
				new_team 	= Team(team_name = c_team_name,
									season = c_season,
									captain = c_captain
									)
				new_team.save()
				message		= c_team_name + " successfully added"
			
			messages.add_message(self.request, messages.INFO, message)
		
			return HttpResponseRedirect('/shooter/administration/newteam/')
		else:
			return self.render_to_response(self.get_context_data(form=form))

"""
class TeamFormView2(UserPassesTestMixin, View):

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()
		
	template_name 	= 'shooter/newseason.html'
	initial		= []
	now 		= datetime.datetime.now().year
	form_count 	= 2
	#TeamFormSet = formset_factory(TeamForm, formset=BaseTeamFormSet, extra=form_count)
	TeamFormSet = formset_factory(TeamForm, extra=form_count)
	#TeamFormSet = modelformset_factory(Team, fields=('team_name', 'season', 'captain'))

	for n in range(1,form_count):
		initial.append({'season': now})

	def get(self, request, *args, **kwargs):
		team_formset = self.TeamFormSet
		
		return render(request, self.template_name, {'form': team_formset})

	def post(self, request, *args, **kwargs):
		team_formset = self.TeamFormSet(request.POST)
		
		if team_formset.is_valid():
			new_teams = []
			
			for f in team_formset:
				c_team_name = f.cleaned_data.get('team_name')
				c_captain	= f.cleaned_data.get('captain')
				c_season	= f.cleaned_data.get('season')
				
				if c_team_name and c_captain and c_season:
					new_teams.append(Team(team_name=c_team_name, captain=c_captain, season=c_season))
					
			#TODO: Validate whether the team already exists to avoid duplication
			#team_object = Team.objects.filter(team_name=c_team_name, season=c_season).exists()
					
			try:
				with transaction.atomic():
					Team.objects.bulk_create(new_teams)
					
					messages.add_message(self.request, messages.INFO, "Team(s) added successfully")
					
			except IntegrityError:
				messages.add_message(self.request, messages.INFO, "ERROR: Problem saving team(s)")
				return HttpResponseRedirect('/shooter/administration/newseason/')
		
		else:
			message = "Form invalid"
			messages.add_message(self.request, messages.INFO, message)

			return HttpResponseRedirect('/shooter/administration/newseason/')
		
		return render(request, self.template_name, {'form': team_formset})