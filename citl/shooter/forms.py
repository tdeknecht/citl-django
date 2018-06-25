from django import forms

class TeamForm(forms.Form):

	team_name = forms.CharField(label='Team Name', max_length=100)
	season = forms.IntegerField(label="Season")