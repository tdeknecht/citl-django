from django import forms

class TeamForm(forms.Form):

	team_name 	= forms.CharField(label='Team Name', max_length=100)
	captain		= forms.CharField(label='Captain')
	season 		= forms.IntegerField(label="Season")
	
class ShooterForm(forms.Form):
	
	first_name	= forms.CharField(label='First Name', max_length=50)
	last_name	= forms.CharField(label='Last Name', max_length=50)
	email		= forms.EmailField(label='Email', max_length=100)
	rookie		= forms.BooleanField(label='Rookie',required=False)
	guest		= forms.BooleanField(label='Guest',required=False)
	
class ScoreForm(forms.Form):

	shooter		= forms.CharField(label='Shooter Name')