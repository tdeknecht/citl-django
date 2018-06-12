import datetime

from django.db import models
from django.utils import timezone


class Weekly_Score(models.Model):

	def __str__(self):
		return self.date + " " + self.week
		
	#def was_published_recently(self):
	#	return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
		
	date = models.models.DateTimeField()
	shooter_id = ForeignKey(Shooter, on_delete=models.CASCADE)
	week = IntegerField()
	bunker_one = IntegerField()
	bunker_two = IntegerField()