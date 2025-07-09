# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture',
            'bio',
            'location',
            'website',
            'twitter',
            'linkedin',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
