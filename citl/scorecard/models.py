import datetime

from django.db import models
from django.utils import timezone

from shooter.models import Season


class Weekly_Score(models.Model):

	def __str__(self):
		return self.date + " " + self.week
		
	date = models.DateTimeField()
	season = models.ForeignKey(Season, on_delete=models.CASCADE)
	week = models.IntegerField()
	bunker_one = models.IntegerField()
	bunker_two = models.IntegerField()