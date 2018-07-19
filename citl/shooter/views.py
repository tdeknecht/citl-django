# Views

import sys
import datetime

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import render
from django.forms import formset_factory
from django.views import View
from django.http import HttpResponseRedirect

from .models import Shooter, Team, Score
from .forms import TeamForm, TeamChoiceForm, ShooterForm, ScoreForm

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

	template_name = 'shooter/season.html'

	def get(self, request, year):

		season = Team.objects.values('season', 'team_name').filter(season=year).distinct()

		context = {
			'season': season,
			'year': year,
		}

		return render(request, self.template_name, context)

class ScorecardView(View):
	def get(self, request, year, team):

		week_range = range(0,16)

		scores = Score.objects \
				.values('shooter__first_name', 'shooter__last_name', 'week', 'bunker_one', 'bunker_two', 'average',
						'team__captain__first_name', 'team__captain__last_name' ) \
				.filter(team__season=year, team__team_name=team) \
				.order_by('shooter__first_name', 'week')

		scorecard = {}
		for score in scores:
			personName = score['shooter__first_name'] + " " + score['shooter__last_name']
			if personName not in scorecard:
				scorecard[personName] = { 'weeks': dict.fromkeys(week_range,'-'),
										  'count': 0, 'average': score['average'] }

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

	template_name = 'shooter/administration.html'
	this_season = datetime.datetime.now().year

	def test_func(self):
		"""Validate user viewing this page has permission
		"""
		return self.request.user.groups.filter(name='League Administrators').exists()

	def get(self, request):

		season = Team.objects.values('team_name').order_by('team_name').filter(season=self.this_season)

		context = {
			'season': season,
		}

		return render(request, self.template_name, context)

# FORM VIEWS

class NewTeamView(UserPassesTestMixin, View):

	template_name 	= 'shooter/newteam.html'
	this_season		= datetime.datetime.now().year
	extra_forms		= 14
	TeamForm		= TeamForm
	ShooterFormSet	= formset_factory(ShooterForm, min_num=1, validate_min=True, extra=extra_forms)

	def test_func(self):
		"""Validate user viewing this page has permission
		"""
		return self.request.user.groups.filter(name='League Administrators').exists()

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
						shooter = Shooter(first_name=c_first_name, last_name=c_last_name, email=c_email,
										  rookie=c_rookie, guest=c_guest)

						# Check to see if the name was entered twice in the same form
						if shooter not in new_shooters:

							# Check to see if the shooter already exists in the league
							# Q: How do I handle multiple shooters with the same name in the league? Could get messy...
							if Shooter.objects.filter(first_name=c_first_name, last_name=c_last_name).exists():
								messages.add_message(self.request, messages.WARNING, c_first_name + " " + c_last_name +
													 " already exists in the league")
							else:
								shooter.save()
								ScoreInit = Score(shooter=shooter, team=new_team, date=datetime.datetime.now().date())
								ScoreInit.save()
						else:
							messages.add_message(self.request, messages.WARNING, c_first_name + " " + c_last_name +
												 " was entered more than once on the form")
			else:
				messages.add_message(self.request, messages.ERROR, "A Team Name and Season must be entered")

		else:
			messages.add_message(self.request, messages.ERROR, "Validation error")

		# Doing it this way will blank out the fields after POST
		return HttpResponseRedirect('/shooter/administration/newteam/')

		# Doing it this way will keep the fields populated after POST
		# return render(request, self.template_name, {'team_form': team_form, 'shooter_formset': shooter_formset})

class NewShooterView(UserPassesTestMixin, View):

	template_name = 'shooter/newshooter.html'
	this_season = datetime.datetime.now().year
	team_form = TeamChoiceForm
	# team_form.fields['team_name'].initial = Team.objects.filter(season=this_season)
	shooter_form = ShooterForm

	def test_func(self):
		return self.request.user.groups.filter(name='League Administrators').exists()

	def get(self, request):
		"""On initial GET, return form and formset for Team and Shooter
		"""
		team_form = self.team_form
		shooter_form = self.shooter_form

		return render(request, self.template_name, {'team_form': team_form, 'shooter_form': shooter_form})

	def post(self, request):
		"""On POST, collect information in the forms, validate it, and add it to the database
		"""
		team_form	= self.team_form(request.POST)
		shooter_form = self.shooter_form(request.POST)

		# Basic form validation conditional
		if team_form.is_valid() and shooter_form.is_valid():

			c_team_name = team_form.cleaned_data['team_name']
			c_first_name = shooter_form.cleaned_data['first_name']
			c_last_name = shooter_form.cleaned_data['last_name']
			c_email = shooter_form.cleaned_data['email']
			c_rookie = shooter_form.cleaned_data['rookie']
			c_guest = shooter_form.cleaned_data['rookie']

			# Need to have a Team Name, and First and Last name. The rest is optional or defaulted
			if c_team_name and c_first_name and c_last_name:
				shooter = Shooter(first_name=c_first_name, last_name=c_last_name, email=c_email,
								  rookie=c_rookie, guest=c_guest)

				# Check to see if the shooter already exists in the league; brute force...
				# Q: How do I handle multiple shooters with the same name in the league? Could get messy...
				if Shooter.objects.filter(first_name=c_first_name, last_name=c_last_name).exists():
					messages.add_message(self.request, messages.WARNING,
										 c_first_name + " " + c_last_name + " already exists in the league")

				# I don't need to check if the team exists because I pull it from Team model in forms.py

				# If the shooter is new, save the shooter and give them a WEEK0 score
				else:
					team = Team.objects.get(team_name=c_team_name, season=self.this_season)
					shooter.save()
					ScoreInit = Score(shooter=shooter, team=team, date=datetime.datetime.now().date())
					ScoreInit.save()
					messages.add_message(self.request, messages.INFO, c_first_name + " " + c_last_name +
										 " added to " + c_team_name)
		else:
			messages.add_message(self.request, messages.ERROR, "Validation error")

		return HttpResponseRedirect('/shooter/administration/newshooter/')

class NewScoreView(UserPassesTestMixin, View):

	template_name = 'shooter/newscore.html'

	def test_func(self):

		return self.request.user.groups.filter(name='League Administrators').exists()

	def get(self, request, team):

		return render(request, self.template_name, {'team': team})

class TestView(View):
	def get(self, request):

		context = {
			'test': "Test"
		}

		return render(request, 'shooter/test.html', context)