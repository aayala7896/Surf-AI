from api.models import Video
from api.models import myuser
from django import forms


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ["title", "url"]

class JoinForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'newpassword', 'placeholder': "Password"}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'size': '30', 'placeholder': "Email"}))

    class Meta:
        model = myuser
        fields = ('first_name', 'last_name', 'username', 'email', 'password')
        help_texts = {'username': None}
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
        }

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder:': "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': "Password"}))

