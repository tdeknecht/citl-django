# Views

import sys
import datetime

from collections import Counter

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import render
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from django.views import View
from django.http import HttpResponseRedirect
from django.db import models
from django.db.models import F

from .models import Shooter, Team, Score
from .forms import TeamForm, TeamChoiceForm, ShooterForm, ScoreFormTeam, ScoreFormWeek


class SeasonsView(View):

	template_name = 'shooter/seasons.html'

	def get(self, request):

		# In the absense of something yet discovered, I used Extract. This is only available with certain databases!
		all_season = Score.objects \
			.annotate(season=models.functions.Extract('date', 'year')) \
			.values('season','team__team_name') \
			.order_by('-season') \
			.distinct()

		print(all_season)

		context = {
			'all_season': all_season,
			'current_year': datetime.datetime.now().year,
		}

		return render(request, self.template_name, context)


class SeasonView(View):

	template_name = 'shooter/season.html'

	def get(self, request, year):

		season = Score.objects \
			.annotate(season=models.functions.Extract('date', 'year')) \
			.values('season', 'team__team_name').filter(season=year).distinct()

		context = {
			'season': season,
			'year': year,
		}

		return render(request, self.template_name, context)


class ScorecardView(View):
	def get(self, request, year, team):

		week_range = range(0,16)

		scores = Score.objects \
				.values('shooter__first_name', 'shooter__last_name', 'week', 'bunker_one', 'bunker_two') \
				.filter(team__team_name=team, date__year=year) \
				.order_by('shooter__last_name', 'shooter__first_name', 'week')

		# Init some vars for the upcoming loop
		scorecard = {}
		for score in scores:
			personName = score['shooter__first_name'] + " " + score['shooter__last_name']

			# For each new person pulled from the Team, build their scorecard line and calculate average
			# Count var is initializes at -1 because WEEK0 is NOT counted toward weeks participated
			if personName not in scorecard:
				scorecard[personName] = { 'weeks': dict.fromkeys(week_range,0), 'count': -1, 'average': 0 }

			if (score['bunker_one'] + score['bunker_two']) > 0:
				# Add the two bunkers for that week
				scorecard[personName]['weeks'][score['week']] = score['bunker_one'] + score['bunker_two']

				# Bump the Weeks Shot count
				scorecard[personName]['count'] += 1

		# Calculate shooters' averages
		for person, values in scorecard.items():
			# scores = {k: v for k, v in values['weeks'].items() if v != '-'} # used this when i had '-' as placeholders
			scores = {k: v for k, v in values['weeks'].items() if v != 0}
			values['average'] = shooterAverage(scores)

		# TODO: Add 'Total Targets', 'Rank Points', and 'Bonus Points' table line in scorecard.html
		# Calculate total targets row
		total_targets = totalTargets(scorecard)

		context = {
			'scores': scorecard,
			'team': team,
			'weekRange': week_range,
			'season': year,
			'totalTargets': total_targets,
		}

		return render(request, 'shooter/scorecard.html', context)


class AdministrationView(UserPassesTestMixin, View):

	template_name = 'shooter/administration.html'

	def test_func(self):
		"""Validate user viewing this page has permissions
		"""
		return self.request.user.groups.filter(name='league_admin_g').exists()

	def get(self, request):

		season = Score.objects \
			.annotate(season=models.functions.Extract('date', 'year')) \
			.values('team__team_name') \
			.order_by('team__team_name') \
			.distinct()

		#season = Score.objects.values('team').order_by('team').distinct()

		# TODO: Pretty sure I removed any use of Season. Come back and clean this up.
		context = {
			'season': season,
		}

		return render(request, self.template_name, context)

	def post(self, request, *args, **kwargs):
		print("POST")

		scores = Score.objects \
				.values('shooter__first_name', 'shooter__last_name', 'week', 'bunker_one', 'bunker_two', \
					    'team__team_name') \
				.filter(date__year=datetime.datetime.now().year) \
				.order_by('shooter__last_name', 'shooter__first_name', 'week')

		for team in scores:
			print(team['team__team_name'])
		#print(scores)

		return HttpResponseRedirect('/shooter/administration/')

# FORM VIEWS

class NewTeamView(UserPassesTestMixin, View):

	template_name 	= 'shooter/newteam.html'
	TeamForm		= TeamForm

	def test_func(self):
		"""Validate user viewing this page has permission
		"""
		return self.request.user.groups.filter(name='league_admin_g').exists()

	def get(self, request, *args, **kwargs):
		"""On initial GET, return forms
		"""
		team_form = self.TeamForm

		return render(request, self.template_name, {'team_form': team_form})

	def post(self, request, *args, **kwargs):
		"""On POST, collect information in the forms, validate it, and add it to the database
		"""
		team_form = self.TeamForm(request.POST)

		# Basic form validation conditional
		if team_form.is_valid():

			c_team_name = team_form.cleaned_data.get('team_name')

			if c_team_name:
				new_team = Team(team_name=c_team_name)

				if Team.objects.filter(team_name=c_team_name).exists():
					messages.add_message(self.request, messages.ERROR, "Team " + c_team_name + " already exists")
					return HttpResponseRedirect('/shooter/administration/newteam/')
				else:
					new_team.save()
					messages.add_message(self.request, messages.INFO, "Successfully added team " + str(c_team_name))
			else:
				messages.add_message(self.request, messages.ERROR, "A Team Name must be entered")

		else:
			messages.add_message(self.request, messages.ERROR, "Validation error")

		# Doing it this way will blank out the fields after POST
		return HttpResponseRedirect('/shooter/administration/newteam/')

		# Doing it this way will keep the fields populated after POST
		# return render(request, self.template_name, {'team_form': team_form, 'shooter_formset': shooter_formset})


class NewShooterView(UserPassesTestMixin, View):

	template_name = 'shooter/newshooter.html'
	#this_season = datetime.datetime.now().year
	team_form = TeamChoiceForm
	shooter_form = ShooterForm

	def test_func(self):
		return self.request.user.groups.filter(name='league_admin_g').exists()

	def get(self, request):
		"""On initial GET, return forms
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
			c_captain = shooter_form.cleaned_data['captain']
			c_rookie = shooter_form.cleaned_data['rookie']
			c_guest = shooter_form.cleaned_data['guest']

			# Need to have a Team Name, and First and Last name. The rest is optional or defaulted
			if c_team_name and c_first_name and c_last_name:
				shooter = Shooter(first_name=c_first_name, last_name=c_last_name, email=c_email, captain=c_captain,
								  rookie=c_rookie, guest=c_guest)

				# Check to see if the shooter already exists in the league; brute force...
				# TODO: How do I handle multiple shooters with the same name in the league? Could get messy.
				#		Right now I do it via a unique email address.
				if Shooter.objects.filter(first_name=c_first_name, last_name=c_last_name, email=c_email).exists():
					messages.add_message(self.request, messages.WARNING,
										 c_first_name + " " + c_last_name + " already exists in the league")

				# I don't need to check if the team exists because I pull it from Team model in forms.py

				# If the shooter is new, save the shooter and give them a WEEK0 score (default TOTAL 35).
				# I could create default values for WEEK0 via the Model, but this gives me more flexibility.
				else:
					team = Team.objects.get(team_name=c_team_name)
					shooter.save()
					ScoreInit = Score(shooter=shooter, team=team, date=datetime.datetime.now().date(),
									bunker_one=1, bunker_two=34)
					ScoreInit.save()
					messages.add_message(self.request, messages.INFO, c_first_name + " " + c_last_name +
										 " added to " + c_team_name)
		else:
			messages.add_message(self.request, messages.ERROR, "Validation error")

		return HttpResponseRedirect('/shooter/administration/newshooter/')


class NewScoreView(UserPassesTestMixin, View):

	template_name = 'shooter/newscore.html'
	this_season = datetime.datetime.now().year
	score_form_team = ScoreFormTeam
	score_formset_week = modelformset_factory(Score, form=ScoreFormWeek)

	def test_func(self):

		return self.request.user.groups.filter(name='league_admin_g').exists()

	def get(self, request, team):
		"""On initial GET, return forms
		"""

		# initialize the first bit of the form: date and week. We only need to enter this once per team
		date_init = {
			'date': datetime.datetime.today(),
			'week': 0,
		}

		# get the team_id for the team_name that was passed via URLs
		team_id = Team.objects.get(team_name=team)
		# pull the shooters into a queryset to prepoulate the modelformset, filtering on current year and team_id
		qset = Score.objects \
			.filter(date__year=self.this_season, team=team_id) \
			.order_by('shooter__last_name', 'shooter__first_name') \
			.distinct('shooter__last_name', 'shooter__first_name')

		# initialize the scores to 0 for the form being displayed
		for shooter in qset:
			shooter.bunker_one, shooter.bunker_two = 0,0

		# build the forms with their respective initalized data
		score_form_team = self.score_form_team(initial=date_init)
		score_formset_week = self.score_formset_week(queryset=qset)

		# TODO: Make it so not all the shooter names in the league pop up in the dropdown list. Use below as guide.
		#for form in score_formset_week:
			#form.fields['shooter'].queryset = Score.objects.filter(team__team_name=team)

		context = {
			'score_form_team': score_form_team,
			'score_formset_week': score_formset_week,
			'team': team,
		}

		return render(request, self.template_name, context)

	def post(self, request, team):
		"""On POST, validate data entry and save to back end
		"""

		score_form_team = self.score_form_team(request.POST)
		score_formset_week = self.score_formset_week(request.POST)

		if score_form_team.is_valid() and score_formset_week.is_valid():

			c_date = score_form_team.cleaned_data.get('date')
			c_week = score_form_team.cleaned_data.get('week')
			team_id = Team.objects.get(team_name=team)

			for f in score_formset_week:
				# Don't do anything with fields that don't have a shooter selected
				if f.cleaned_data.get('shooter') is not None:
					c_shooter = f.cleaned_data.get('shooter')
					c_b1 = f.cleaned_data.get('bunker_one')
					c_b2 = f.cleaned_data.get('bunker_two')

					# Use this previous logic to improve performance by moving average to its own database
					# bunker_total = [c_b1 + c_b2]
					# sum all current bunkers from this year to calculate average later on
					# bunker_qset = Score.objects \
					# 	.annotate(season=models.functions.Extract('date', 'year'),
					#			  bunker_total=F('bunker_one') + F('bunker_two')) \
					#	.filter(season=self.this_season, team=team_id, shooter=c_shooter)

					# add the queried and summed bunkers to the bunker list
					# for q in bunker_qset:
					#	bunker_total.append(q.bunker_total)

					# calculate average based on the shooter and the current season
					# average = sum(bunker_total) / float(len(bunker_total))

					# if the scores are zeroes, don't add a new score
					if (c_b1 + c_b2) == 0:
						continue
					# check to see if a score already exists for the year and week. If it does, warn me of duplication
					elif Score.objects.filter(shooter=c_shooter, week=c_week, date__year=c_date.year).exists():
						messages.add_message(self.request, messages.WARNING,
											 str(c_shooter) + " already has a score for this week. Score not added.")
					# else add a new score to the Score model
					else:
						# build the new score to add to the database
						new_score = Score(shooter=c_shooter, team=team_id, date=c_date, week=c_week,
										  bunker_one=c_b1, bunker_two=c_b2)

						new_score.save()
						messages.add_message(self.request, messages.INFO, "Score added for " + str(c_shooter))
		else:
			print("ERROR: NEWSCORE_VALIDATION_ERROR...")
			print("Header", score_form_team.errors)
			print("Scores", score_formset_week.errors)
			for e in score_formset_week.errors:
				print(e)
			messages.add_message(self.request, messages.ERROR, "Validation error. Check server logs for details.")

		context = {
			'score_form_team': score_form_team,
			'score_formset_week': score_formset_week,
			'team': team,
		}

		# return render(request, self.template_name, context)
		return HttpResponseRedirect('/shooter/administration/')


class TestView(View):
	def get(self, request):

		context = {
			'test': "Test"
		}

		return render(request, 'shooter/test.html', context)

# Special formulas for calculating averages
def shooterAverage(scores):
	# TODO: Move this to newScore with a dedicated table on the back end. Avoid calculating on each page view

	# TODO: Could be a more Pythonic way of doing this than creating an entirely new dictionary.
	# A temporary dictionary that drops W0 to allow for special league average formulas
	scores_noW0 = {k:v for k,v in scores.items() if k != 0}

	# If less than two scores between W1 and W15: average(W0:W15)
	if len(scores_noW0.values()) < 2:
		return round(float(sum(scores.values())) / max(len(scores.values()), 1),2)
	# Else average(W1:W15)
	else:
		return round(float(sum(scores_noW0.values())) / max(len(scores_noW0.values()), 1),2)

# Calculate Total Targets row in Scorecard
def totalTargets(scorecard):
	r = range(0, 16)

	t1 = {'total_targets': dict.fromkeys(r, 0)}
	t2 = {}

	for shooter,v in scorecard.items():
		t2 = Counter(t2) + Counter(v['weeks'])

	total_targets = {**t1['total_targets'], **t2}

	return(total_targets)
