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
		return str(self.season) + ":" + self.team_name

	team_name = models.CharField(max_length=100)
	captain = models.ForeignKey(Shooter, blank=True, null=True, on_delete=models.CASCADE)
	season = models.IntegerField()
	
class Score(models.Model):

	def __str__(self):
		return str(self.date) + " " + str(self.week) + ":" + self.shooter.first_name
		
	shooter = models.ForeignKey(Shooter, on_delete=models.CASCADE)
	team = models.ForeignKey(Team, on_delete=models.CASCADE)
	date = models.DateField(blank=True, null=True)
	week = models.IntegerField(default=0)
	bunker_one = models.IntegerField(default=0.0)
	bunker_two = models.IntegerField(default=0.0)
	average = models.FloatField(default=35.0)