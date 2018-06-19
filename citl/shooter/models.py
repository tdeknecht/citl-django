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
	rookie = models.BooleanField()
	guest = models.BooleanField()
	captain = models.BooleanField(default=False)
	average = models.FloatField()
	
class Team(models.Model):

	def __str__(self):
		return self.team_name
		
	team_name = models.CharField(max_length=100)
	
class Score(models.Model):

	def __str__(self):
		return str(self.date) + " " + str(self.week)
		
	date = models.DateField()
	week = models.IntegerField()
	bunker_one = models.IntegerField()
	bunker_two = models.IntegerField()
	
class Season(models.Model):
	
	def __str__(self):
		return str(self.season_year) + " " + str(self.shooter)
		#return str(self.season_year)
		
	season_year = models.IntegerField()
	shooter = models.ForeignKey(Shooter, on_delete=models.CASCADE)
	team = models.ForeignKey(Team, on_delete=models.CASCADE)
	score = models.ForeignKey(Score, on_delete=models.CASCADE)