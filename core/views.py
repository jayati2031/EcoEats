from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DeleteView
from .utils import send_email_notification 
from django.shortcuts import render, redirect
from .forms import FoodItemForm, RecipeForm
from .models import FoodItem, Recipe, UserActivity, Notification
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .spoonacular_service import get_recipes_by_ingredients, get_recipe_details
import csv
from django.http import HttpResponse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now

# Register view
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        
        # Check if the form is valid
        if form.is_valid():
            try:
                # Save the user and get the username and email
                user = form.save()
                username = form.cleaned_data.get('username')
                email = form.cleaned_data.get('email')

                 # Ensure the email is being saved properly
                if email:
                    user.email = email
                    user.save()
                
                # Display success message
                messages.success(request, f'Account created for {username}!')

                # Redirect to the login page
                return redirect('login')
            except Exception as e:
                # Log the error and display an error message
                print(f"Error while registering the user: {e}")
                messages.error(request, "An error occurred while creating your account. Please try again.")
        else:
            # If form is not valid, display the form errors
            print(f"Form errors: {form.errors}")
            for field, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"Error in {field}: {error}")

    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')  
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request, username=username, password=password)
            if user is None:
                messages.error(request, "Username and password do not match.")
            else:
                messages.error(request, "There was an error with your login credentials.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='/login')
def dashboard(request):
    # Get all the food items related to the logged-in user
    food_items = request.user.food_items.all()
    
    # Get the recipes related to the logged-in user
    recipes = request.user.recipes.all()

    # Filter food items that are expiring soon (within the next 3 days)
    expiring_soon = [item for item in food_items if item.is_expiring_soon()]

    # Pass the expiring_soon list to the template
    return render(request, 'dashboard.html', {
        'food_items': food_items,
        'recipes': recipes,
        'expiring_soon': expiring_soon,  # Pass the expiring_soon list to the template
    })

@login_required(login_url='/login')
# def food_item_list(request):
#     food_items = request.user.food_items.all()
#     return render(request, 'food_item_list.html', {'food_items': food_items})

def food_item_list(request):
    food_items = FoodItem.objects.all()

    categorized_food_items = {}
    for food_item in food_items:
        if food_item.category not in categorized_food_items:
            categorized_food_items[food_item.category] = []
        categorized_food_items[food_item.category].append(food_item)

    return render(request, 'food_item_list.html', {
        'categorized_food_items': categorized_food_items
    })

@login_required(login_url='/login')
def add_food_item(request):
    if request.method == "POST":
        form = FoodItemForm(request.POST)
        if form.is_valid():
            food_item = form.save(commit=False)
            food_item.user = request.user
            food_item.save()
            # Log the action
            UserActivity.objects.create(user=request.user, action=f"Added food item: {food_item.name}")
            messages.success(request, 'Food Item added successfully!')
            return redirect('food_item_list')
    else:
        form = FoodItemForm()
    return render(request, 'add_food_item.html', {'form': form})

# Update View for Food Item
class FoodItemUpdateView(UpdateView):
    model = FoodItem
    form_class = FoodItemForm
    template_name = 'update_fooditem.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        UserActivity.objects.create(user=self.request.user, action=f"Updated food item: {self.object.name}")
        return response

    def get_success_url(self):
        return reverse_lazy('food_item_list')  # Redirect to the food item list page after updating

# Delete View for Food Item
class FoodItemDeleteView(DeleteView):
    model = FoodItem
    template_name = 'fooditem_confirm_delete.html'
    success_url = reverse_lazy('food_item_list')  # Redirect to the food item list page after deleting

    def delete(self, request, *args, **kwargs):
        food_item = self.get_object()
        UserActivity.objects.create(user=request.user, action=f"Deleted food item: {food_item.name}")
        return super().delete(request, *args, **kwargs)

@login_required(login_url='/login')
def recipes(request):
    if request.method == "POST":
        # Get selected food items from the form
        selected_items = request.POST.getlist('selected_items')
        if not selected_items:
            return render(request, 'recipe_list.html', {'error': 'No items selected!', 'recipes': []})

        ingredients = ",".join(selected_items)

        # Call the Spoonacular API to fetch recipes
        recipe_results = get_recipes_by_ingredients(ingredients)
        return render(request, 'recipe_results.html', {'recipes': recipe_results})

    # Fetch the top 10 food items nearing expiry
    food_items = FoodItem.objects.filter(expiration_date__isnull=False).order_by('expiration_date')[:10]
    return render(request, 'recipe_list.html', {'food_items': food_items})

@login_required(login_url='/login')
def recipe_detail(request, recipe_id):
    recipe = get_recipe_details(recipe_id)
    if recipe:
        return render(request, 'recipe_details.html', {'recipe': recipe})
    else:
        return render(request, 'recipe_details.html', {'error': 'Recipe details not found.'})

@login_required
def recipe_list(request):
    recipes = request.user.recipes.all()
    return render(request, 'recipe_list.html', {'recipes': recipes})

@login_required(login_url='/login')
def add_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.user = request.user
            recipe.save()
            # Log the action
            UserActivity.objects.create(user=request.user, action=f"Added recipe: {recipe.title}")
            messages.success(request, 'Recipe added successfully!')
            return redirect('recipe_list')
    else:
        form = RecipeForm()
    return render(request, 'add_recipe.html', {'form': form})

def export_food_items(request):
    food_items = FoodItem.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="food_items.csv"'

    writer = csv.writer(response)

    writer.writerow(['ID', 'Name', 'Description', 'Category', 'Quantity', 'Expiration Date', 'Priority', 'Refrigerated', 'Added On'])

    # Write the data rows
    for food_item in food_items:
        formatted_expiration_date = food_item.expiration_date.strftime('%Y-%m-%d')
        
        writer.writerow([
            food_item.id, 
            food_item.name, 
            food_item.description, 
            food_item.get_category_display(),  # For human-readable category name
            food_item.quantity, 
            formatted_expiration_date,  # Use formatted date
            food_item.get_priority_display(),  # For human-readable priority name
            'Yes' if food_item.refrigerated else 'No',  # For boolean to human-readable
            food_item.added_on.strftime('%Y-%m-%d %H:%M:%S')  # Format added_on as a datetime string
        ])

    return response

@login_required(login_url='/login')
def user_history(request):
    # Fetch activity logs
    activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:3]

    # Fetch visit history from session
    visit_history = request.session.get('visit_history', [])

    return render(request, 'user_history.html', {
        'activities': activities,
        'visit_history': visit_history,
    })

@receiver(post_save, sender=FoodItem)
def check_food_item_expiry(sender, instance, created, **kwargs):
    try:
        if created:
            print(f"DEBUG: New FoodItem created: {instance.name} (Expiration: {instance.expiration_date})")
        
        if instance.is_expiring_soon():
            print(f"DEBUG: FoodItem '{instance.name}' is expiring soon.")

            # Check and print user email
            user_email = instance.user.email
            if not user_email:
                print(f"ERROR: User {instance.user.username} does not have an email address set.")
                return  # Skip sending email

            print(f"DEBUG: User email for FoodItem '{instance.name}': {user_email}")

            # Send email
            subject = f"Food Expiry Alert: {instance.name}"
            message = (
                f"Hello {instance.user.username},\n\n"
                f"Your food item '{instance.name}' is expiring soon! "
                f"It will expire on {instance.expiration_date}.\n\n"
                "Please use it soon or consider donating it to avoid waste.\n\n"
                "Regards,\nEcoEats Team"
            )
            recipient_list = [user_email]

            print(f"DEBUG: Preparing to send email to {recipient_list}")
            send_email_notification(subject, message, recipient_list)

            # Create Notification
            Notification.objects.create(
                user=instance.user,
                food_item=instance,
                message=f"Your food item '{instance.name}' is expiring soon! Expiry date: {instance.expiration_date}",
            )
            print(f"DEBUG: Notification created for {instance.name}.")
        else:
            print(f"DEBUG: FoodItem '{instance.name}' is not expiring soon.")
    except Exception as e:
        print(f"ERROR: An error occurred in the check_food_item_expiry signal: {e}")

    if created:
        # Check if the food item is expiring soon (within 3 days)
        if instance.is_expiring_soon():
            # Sending an email notification
            subject = f"Food Expiry Alert: {instance.name}"
            message = (
                f"Hello {instance.user.username},\n\n"
                f"Your food item '{instance.name}' is expiring soon! "
                f"It will expire on {instance.expiration_date}.\n\n"
                "Please use it soon or consider donating it to avoid waste.\n\n"
                "Regards,\nEcoEats Team"
            )
            recipient_list = [instance.user.email]

            # Send email notification to the user
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                )
                print(f"Notification sent to {instance.user.email} for {instance.name}")
            except Exception as e:
                print(f"Error sending email: {e}")