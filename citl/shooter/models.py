# Shooter models

import datetime

from django.utils import timezone
from django.db import models

class Shooter(models.Model):

	def __str__(self):
		shooter_name = self.first_name + " " + self.last_name
		return shooter_name
	
	first_name = models.CharField(max_length=50)
	last_name = models.CharField(max_length=50)
	email = models.EmailField(max_length=100)
	rookie = models.BooleanField(default=False)
	guest = models.BooleanField(default=False)
	
class Team(models.Model):

	def __str__(self):
		return self.team_name

	team_name = models.CharField(max_length=100)
	captain = models.ForeignKey(Shooter, blank=True, null=True, on_delete=models.CASCADE)
	season = models.IntegerField() # remove this and update models. It's no longer needed
	
class Score(models.Model):

	def __str__(self):
		return str(self.team) + ": " \
				+ str(self.shooter) + " " \
				+ str(self.date) + " " \
				+ str(self.week) + " " \
				+ str(self.bunker_one) + " " + str(self.bunker_two)
		
	WEEK_CHOICES = []
	for n in range(0,16):
		#WEEK_CHOICES.append(("W"+str(n), "W"+str(n)))
		WEEK_CHOICES.append((n, "W"+str(n)))		
		
	shooter = models.ForeignKey(Shooter, on_delete=models.CASCADE)
	team = models.ForeignKey(Team, on_delete=models.CASCADE)
	date = models.DateField(blank=True, null=True)
	week = models.IntegerField(choices=WEEK_CHOICES, default=0)
	bunker_one = models.IntegerField(default=0)
	bunker_two = models.IntegerField(default=0)
	average = models.FloatField(default=35.0)