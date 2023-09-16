"""
This is where you handle requests (front-end)
Also, you can modify models here (back-end)
"""

from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from recipes.forms import ReviewForm

from .forms import LoginForm, RegisterForm
from .models import Member
from recipes.models import Recipe, Review

# Create your views here.


def members(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        return render(request, "login_bootstrap.html", {"form": form})
    return HttpResponse("Hello world!")


# Form processing code reference: https://docs.djangoproject.com/en/4.2/topics/forms/
def login_request(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("recipes:index")
            else:
                messages.warning(request, "User password mismatch")
        else:
            messages.warning(request, "User not found")
        # redirect to a new URL:
        return redirect("recipes:index")
    # if a GET (or any other method) we'll create a blank form
    else:
        form = LoginForm()
        return render(request, "login_bootstrap.html", {"form": form})


def register_request(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required, validation in form class
            username = form.cleaned_data["user_name"]
            password = form.cleaned_data["password"]
            firstname = form.cleaned_data["first_name"]
            lastname = form.cleaned_data["last_name"]
            email = form.cleaned_data["email"]
            # create user
            member = form.save(commit=False)
            user = User.objects.create(
                username=username, first_name=firstname, last_name=lastname, email=email
            )
            user.set_password(password)
            # the user will not be save automatically
            user.save()
            member.user_id = user
            member.save()
            # redirect to a new URL:
            messages.info(request, "User registration success")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
            return redirect("recipes:index")
        else:
            if form.errors:
                for key, value in form.errors.items():
                    messages.error(request, f"{key},{value}")
            return redirect("members:register")
    else:
        form = RegisterForm()
        return render(request, "register_bootstrap.html", {"form": form})


def logout_request(request):
    logout(request)
    return redirect("recipes:index")


def get_profile(request, username):
    user_instance = get_object_or_404(User, username=username)
    member_instance = get_object_or_404(Member, user_id=user_instance)
    recipes = Recipe.objects.filter(owner_id=member_instance)
    reviews = Review.objects.filter(sender_id=member_instance)
    # test for edit permission
    can_edit=False
    # placeholder value
    review_formsets=None
    if member_instance.user_id == request.user:
        can_edit=True
        # render forms for review
        # initalized form factories
        ReviewFormSet = modelformset_factory(
            Review, form=ReviewForm, can_delete=True, extra=0
        )
        # insert queries
        review_formsets = ReviewFormSet(
            queryset=Review.objects.filter(sender_id=member_instance).order_by(
                "-created"
            )
        )
    return render(
        request,
        "profile_bootstrap.html",
        {
            "can_edit": can_edit,
            "userinfo": member_instance,
            "recipes": recipes,
            "reviews": reviews,
            "review_formsets":review_formsets
        },
    )

# pk is user_id
@login_required
def edit_reviews(request, username):
    user_id = get_object_or_404(User, username=username)
    cur_member = get_object_or_404(Member, user_id=user_id)
    # test ownership
    if request.user.username!=username:
        messages.warning("don't change other's comment")
        return redirect('members:profile', username=user_id.username)
    if request.method == "POST":
         # initalized form factories
        ReviewFormSet = modelformset_factory(
            Review, form=ReviewForm, can_delete=True, extra=0
        )
        # insert queries
        review_formsets = ReviewFormSet(request.POST)
        # check whether it's valid:
        if review_formsets.is_valid():
            review_instances=review_formsets.save(commit=False)
            # delte on select, reference:https://docs.djangoproject.com/en/4.2/topics/forms/formsets/#dealing-with-ordering-and-deletion-of-forms
            for obj in review_formsets.deleted_objects:
                obj.delete()
            # check permission
            for review in review_instances:
                if review.sender_id==cur_member:
                    review.save()
            messages.success(request,"edit reviews success")
        else:
            messages.warning(request,"Invalid reviews form")
    return redirect('members:profile', username=user_id.username)

@login_required
def edit_profile(request, username):
    # test consistency
    if request.user.username != username:
        messages.warning(request, "Do not change other's password")
    user_instance = get_object_or_404(User, username=username)
    membmer = get_object_or_404(Member, user_id=user_instance)
    if request.method == "POST":
        profile_form = RegisterForm(request.POST, instance=membmer)
        if profile_form.is_valid():
            # process the data in form.cleaned_data as required, validation in form class
            password = profile_form.cleaned_data["password"]
            user_instance.username = profile_form.cleaned_data["user_name"]
            if len(profile_form.cleaned_data["password"]) > 8:
                user_instance.set_password(password)
            user_instance.firstname = profile_form.cleaned_data["first_name"]
            user_instance.lastname = profile_form.cleaned_data["last_name"]
            user_instance.email = profile_form.cleaned_data["email"]
            # the user will not be save automatically
            user_instance.save()
            profile_form.save()
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
            # redirect to a new URL:
            messages.success(request, "edit profile success")
            return redirect("members:profile", username=username)
        else:
            messages.error(request, "edit profile form invalid")
    else:
        profile_form = RegisterForm(instance=membmer)
    return render(request, "edit_profile_bootstrap.html", {"form": profile_form})
