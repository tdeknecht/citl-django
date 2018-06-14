from django.shortcuts import render
from django.views import View
from django.core import serializers

from .models import Weekly_Score

class ScoreView(View):	
	def get(self, request):
	
		test = "Hello World"		
	
		context = {
			'test': test,
		}		

		return render(request, 'scorecard/index.html', context)