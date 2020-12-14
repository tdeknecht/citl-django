# https://docs.djangoproject.com/en/2.0/intro/tutorial01/

from django.shortcuts import render
from django.views import View

class IndexView(View):	
	def get(self, request):		
	
		context = {
			'home': 'home',
		}		

		return render(request, 'index.html', context)