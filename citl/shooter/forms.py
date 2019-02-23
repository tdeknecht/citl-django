from django import forms
from django.forms.formsets import BaseFormSet

from .models import Shooter, Team, Score

# ModelForms


class TeamForm(forms.ModelForm):
	
	class Meta:
		model = Team
		fields = ['team_name']


class TeamChoiceForm(forms.Form):
	team_name = forms.ChoiceField(choices=[])

	def __init__(self, *args, **kwargs):
		super(TeamChoiceForm, self).__init__(*args, **kwargs)
		self.fields['team_name'].choices = Team.objects.values_list('team_name', 'team_name') \
			.distinct()


class ShooterForm(forms.ModelForm):
	class Meta:
		model	= Shooter
		fields	= ['first_name', 'last_name', 'email', 'rookie', 'guest', 'captain']


class DateInput(forms.DateInput):
	input_type = 'date'


class ScoreFormTeam(forms.ModelForm):
	class Meta:
		model = Score
		fields = ['date', 'week']
		widgets = {
			'date': DateInput(),
		}


class ScoreFormWeek(forms.ModelForm):
	class Meta:
		model = Score
		fields = ['shooter', 'bunker_one', 'bunker_two']

		initial = {
			'bunker_one': 0,
			'bunker_two': 0,
		}

	#def __init__(self, *args, **kwargs):
		#super(ScoreFormWeek, self).__init__(*args, **kwargs)

		#self.fields['shooter'].widget.attrs['disabled'] = True
		#self.fields['bunker_one'].initial = 0


# Forms

"""
class TeamForm(forms.Form):

	team_name 	= forms.CharField(label='Team Name', max_length=100)
	captain		= forms.CharField(label='Captain')
	season 		= forms.IntegerField(label="Season")
"""

"""
class ShooterForm(forms.Form):
	
	first_name	= forms.CharField(label='First Name', max_length=50)
	last_name	= forms.CharField(label='Last Name', max_length=50)
	email		= forms.EmailField(label='Email', max_length=100)
	rookie		= forms.BooleanField(label='Rookie',required=False)
	guest		= forms.BooleanField(label='Guest',required=False)
"""

# BaseFormSets


class BaseTeamFormSet(BaseFormSet):
	def clean(self):
		# Adds validation to check that no two teams have the same name or captain
		# and that all teams have a team name and captain
		if any(self.errors):
			return

		team_names = []
		captains = []
		duplicates = False

		for form in self.forms:
			if form.cleaned_data:
				team_name = form.cleaned_data['team_name']
				captain = form.cleaned_data['captain']

				# Check that no two Teams have the same team name or captain
				if team_name and captain:
					if team_name in team_names:
						duplicates = True
					team_names.append(team_name)

					if captain in captains:
						duplicates = True
					captains.append(captain)

				if duplicates:
					raise forms.ValidationError(
						'Team Names and Captains must be unique',
						code = 'duplicate_entries'
					)

				# Check that all Teams have a team name and captain
				if team_name and not captain:
					raise forms.ValidationError(
						'A Team must have a Captain',
						code = 'missing_captain'
					)
				elif captain and not team_name:
					raise forms.ValidationError(
						'A Captain must be assigned to a Team',
						code='missing_team'
					)
