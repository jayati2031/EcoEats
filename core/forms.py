from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import FoodItem, Recipe

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != password2:
            raise forms.ValidationError("The two password fields must match.")
        return password2


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class FoodItemForm(forms.ModelForm):
    expiration_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})  # This creates a date picker in the form
    )
    class Meta:
        model = FoodItem
        fields = ['name', 'description', 'category', 'quantity', 'expiration_date', 'priority', 'refrigerated']

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'ingredients', 'instructions']