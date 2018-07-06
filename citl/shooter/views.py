# https://docs.djangoproject.com/en/2.0/intro/tutorial01/

import sys
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
		
		if team_form.is_valid() and shooter_formset.is_valid():
		
			c_team_name = team_form.cleaned_data.get('team_name')
			c_season	= team_form.cleaned_data.get('season')
		
			new_shooters = []
			new_scores	= []
			
			if c_team_name and c_season:
				new_team = Team(team_name=c_team_name, season=c_season)
				
				# If a team was entered correctly, continue processing Shooters
				for f in shooter_formset:

					c_first_name 	= f.cleaned_data.get('first_name')
					c_last_name 	= f.cleaned_data.get('last_name')
					c_email 		= f.cleaned_data.get('email')
					c_rookie		= f.cleaned_data.get('rookie')
					c_guest			= f.cleaned_data.get('rookie')
					
					if c_first_name and c_last_name:
						shooter = Shooter(first_name=c_first_name, last_name=c_last_name, email=c_email, rookie=c_rookie, guest=c_guest)
						if shooter not in new_shooters:
							#TODO: I need to check whether the Shooter already exists because i don't want dupes
							#Q: How do I handle multiple shooters with the same name?
							# This is not very efficient, but a new season only occurs once a year. Leaving it for now.
							#if Shooter.objects.filter(first_name=c_first_name, last_name=c_last_name).exists():
							new_shooters.append(shooter)
						else:
							messages.add_message(self.request, messages.WARNING, c_first_name + " " + c_last_name + " was entered more than once")
						
				# Now lets try adding this stuff to our database
				try:				
					with transaction.atomic():	# using an atomic transaction here to ensure a complete bulk commit
						new_team.save()
						Shooter.objects.bulk_create(new_shooters)
						
						messages.add_message(self.request, messages.SUCCESS, "Team and Shooters added successfully")
						
				except IntegrityError as ie:
					type, value, traceback = sys.exc_info()
					messages.add_message(self.request, messages.ERROR, "IntegrityError... " + type + value)
					return render(request, self.template_name, {'team_form': team_form, 'shooter_formset': shooter_formset})
					
				# With a Team and Shooters added to the back end, time to initialize WEEK0 scores to get Shooters on the board and pull in current averages
				#ShooterObjects = Shooter.objects.filter(
			else:
				messages.add_message(self.request, messages.ERROR, "A Team Name and Season must be entered")

		else:
			return HttpResponseRedirect('/shooter/administration/newteam/')
		
		#return HttpResponseRedirect('/shooter/administration/newteam/')		# Doing it this way will blank out the fields after POST
		return render(request, self.template_name, {'team_form': team_form, 'shooter_formset': shooter_formset})		# Doing it this way will keep the fields populated after POST

class TempView(View):
	def get(self, request):
	
		c_first_name 	= 'Tyler'
		c_last_name 	= 'DeKnecht'
		c_email 		= 'tdeknecht@gmail.com'
		c_rookie		= False
		c_guest			= False
		new_shooters	= []
		shooter = Shooter(first_name=c_first_name, last_name=c_last_name, email=c_email, rookie=c_rookie, guest=c_guest)
		new_shooters.append(shooter)
		
		names = ['Tyler','Erin','Pocket']
		
		#Objects = Score.objects.filter(shooter=1)
		#Objects = Shooter.objects.filter(first_name__in=names)
		Objects = Shooter.objects.all().defer('id')
		
		for s in Objects:
			print("s=", s, "list=", new_shooters[0])
			s.id = None
			if s in new_shooters:
				message = "s was in Objects"
			else:
				message = "Your IF didn't work"
		
		context = {
			'objects': Objects,
			'message': message,
			'var1': shooter,
		}
		
		return render(request, 'shooter/temp.html', context)
		
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