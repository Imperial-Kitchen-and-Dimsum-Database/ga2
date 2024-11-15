from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
#this is highkey useless

class CustomUserCreationForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        required=True,
        widget=forms.RadioSelect, 
    )

    class Meta:
        model = CustomUser
        fields = ['phone', 'password1', 'password2', 'user_type']  
