from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

CATEGORY_CHOICES = [
    ('vegetable', 'Vegetable'),
    ('fruit', 'Fruit'),
    ('dairy', 'Dairy'),
    ('meat', 'Meat'),
    ('others', 'Others'),
]

PRIORITY_LEVELS = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferences = models.TextField(blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class FoodItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_items')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='others')
    quantity = models.PositiveIntegerField()
    expiration_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    refrigerated = models.BooleanField(default=False)
    added_on = models.DateTimeField(auto_now_add=True)

    def is_expiring_soon(self):
        return self.expiration_date <= timezone.now().date() + timedelta(days=3)

    def __str__(self):
        return f"{self.name} ({self.quantity}) - {self.category}"

class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    title = models.CharField(max_length=100)
    description = models.TextField()
    ingredients = models.TextField()  # Comma-separated list of ingredients
    instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.food_item.name}"

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"


