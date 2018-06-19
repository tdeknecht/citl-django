# Allows admin priveleges for specific models

from django.contrib import admin

from .models import Shooter, Team, Season, Score

admin.site.register([Shooter, Team, Season, Score])