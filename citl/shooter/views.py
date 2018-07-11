# Views

import sys
import datetime

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import render
from django.forms import formset_factory
from django.views.generic.edit import FormView
from django.views import View
from django.http import HttpResponseRedirect

from .models import Shooter, Team, Score
from .forms import BaseTeamFormSet, TeamForm, ShooterForm, ScoreForm
	
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
	
		week_range = range(0,16)

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
			'weekRange': week_range,
			'season': year,
		}
		
		return render(request, 'shooter/scorecard.html', context)
		
class AdministrationView(UserPassesTestMixin, View):
	"""Landing page for administrative tasks
	"""

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
		
# FORM VIEWS

class NewTeamView(UserPassesTestMixin, View):
	"""View leveraging formset and formset_factory to input a single team and its details, plus any number of shooters.
	A season is required, and all shooters will be initialized with the default values. The Score transaction is what binds them to a team.
	"""
	
	def test_func(self):
		"""Validate user viewing this page has permission
		"""
		return self.request.user.groups.filter(name='League Administrators').exists()
		
	template_name 	= 'shooter/newteam.html'
	this_season		= datetime.datetime.now().year
	extra_forms		= 14
	TeamForm		= TeamForm
	ShooterFormSet	= formset_factory(ShooterForm, min_num=1, validate_min=True, extra=extra_forms)
	
	def get(self, request, *args, **kwargs):
		"""On initial GET, return form and formset for Team and Shooter
		"""
		team_form = self.TeamForm
		shooter_formset = self.ShooterFormSet
		
		return render(request, self.template_name, {'team_form': team_form, 'shooter_formset': shooter_formset})
		
	def post(self, request, *args, **kwargs):
		"""On POST, collect information in the forms, validate it, and add it to the database
		"""
		team_form = self.TeamForm(request.POST)
		shooter_formset = self.ShooterFormSet(request.POST)
		
		# Basic form validation conditional
		if team_form.is_valid() and shooter_formset.is_valid():
		
			c_team_name = team_form.cleaned_data.get('team_name')
			c_season	= team_form.cleaned_data.get('season')
		
			new_shooters = []
			new_scores	= []
			
			# Can't process any Shooters unless we have a team name and season
			if c_team_name and c_season:
				new_team = Team(team_name=c_team_name, season=c_season)
				
				if Team.objects.filter(team_name=c_team_name).exists():
					messages.add_message(self.request, messages.ERROR, "Team " + c_team_name + " already exists")
					return HttpResponseRedirect('/shooter/administration/newteam/')
					
				else:
					new_team.save()
				
				# If a team was entered correctly, continue processing Shooters
				for f in shooter_formset:

					c_first_name 	= f.cleaned_data.get('first_name')
					c_last_name 	= f.cleaned_data.get('last_name')
					c_email 		= f.cleaned_data.get('email')
					c_rookie		= f.cleaned_data.get('rookie')
					c_guest			= f.cleaned_data.get('rookie')
					
					# Need to have a First and Last name. The rest is optional or defaulted
					if c_first_name and c_last_name:
						shooter = Shooter(first_name=c_first_name, last_name=c_last_name, email=c_email, rookie=c_rookie, guest=c_guest)
						
						# Check to see if the name was entered twice in the same form
						if shooter not in new_shooters:

							# Check to see if the shooter already exists in the league
							# Q: How do I handle multiple shooters with the same name in the league? Could get messy...
							if Shooter.objects.filter(first_name=c_first_name, last_name=c_last_name).exists():
								messages.add_message(self.request, messages.WARNING, c_first_name + " " + c_last_name + " already exists")
							else:
								shooter.save()
								ScoreInit = Score(shooter=shooter, team=new_team, date=datetime.datetime.now().date())
								ScoreInit.save()
						else:
							messages.add_message(self.request, messages.WARNING, c_first_name + " " + c_last_name + " was entered more than once on the form")
			else:
				messages.add_message(self.request, messages.ERROR, "A Team Name and Season must be entered")

		else:
			return HttpResponseRedirect('/shooter/administration/newteam/')
		
		return HttpResponseRedirect('/shooter/administration/newteam/')		# Doing it this way will blank out the fields after POST
		#return render(request, self.template_name, {'team_form': team_form, 'shooter_formset': shooter_formset})		# Doing it this way will keep the fields populated after POST

class TestView(View):
	"""Playground View
	"""
	def get(self, request):
		
		context = {
			'test': "Test"
		}
		
		return render(request, 'shooter/test.html', context)
		
class NewShooterFormView(UserPassesTestMixin, FormView):
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

class NewScoreFormView(UserPassesTestMixin, FormView):

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
	
		#form = ScoreForm()
		response = super().form_invalid(form)
		
		return response