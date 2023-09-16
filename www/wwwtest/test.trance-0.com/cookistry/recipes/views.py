"""
This is where you handle requests (front-end)
Also, you can modify models here (back-end)
"""

from math import ceil
from multiprocessing.managers import BaseManager
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required

# get_object_or_404, for those who don't want to write error messages
from django.shortcuts import get_object_or_404, redirect, render
from .models import (
    ProcedureTypeChoice,
    Recipe,
    Procedure,
    Review,
    UnitLengthChoices,
    UnitMassChoices,
    UnitTempChoices,
)
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import RecipeForm, ProcedureForm, ReviewForm
from members.models import Member
from django.db.models import Q


# Create your views here.
def recipes(request):
    recipes_query = Recipe.objects.all()
    if request.user.is_authenticated:
        member = get_object_or_404(Member, user_id=request.user)
        # foreign key filtering reference:https://stackoverflow.com/questions/45393989/django-queryset-filter-foreignkey
        review_query = Review.objects.filter(recipe_id__owner_id=member).order_by(
            "-created"
        )
        recipes_query = sorted(
            recipes_query,
            key=lambda x: 0 if x.score() is None else x.score(),
            reverse=True,
        )
    else:
        review_query = None
    # recipes=[(i,estimate_time(i),ingredients_list(i)[:5],cookware_list(i)[:5]) for i in recipes_query]
    return render(
        request,
        "recipes_list_bootstrap.html",
        {"recipes": recipes_query, "reviews": review_query},
    )


@login_required
def new_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            username = request.user.username
            # The process below is actually not required, django would do that for us, just for fun.
            if (
                User.objects.filter(username=username).exists()
                and Member.objects.filter(
                    user_id=User.objects.get(username=username)
                ).exists()
            ):
                recipe_instance = form.save(commit=False)
                recipe_instance.owner_id = Member.objects.get(
                    user_id=User.objects.get(username=username)
                )
                recipe_instance.save()
                messages.success(request, "Add recipe success!")
                return redirect("recipes:edit_recipe", pk=recipe_instance.id)
            else:
                messages.error(request, "Unknown user detected!")
                return redirect("recipes:new_recipe")
    else:
        form = RecipeForm()
        return render(request, "recipes_add_bootstrap.html", {"form": form})


def get_recipe(request, pk):
    recipe_instance = Recipe.objects.get(pk=pk)
    procedures = Procedure.objects.filter(recipe_id=recipe_instance).order_by("order")
    # placeholder variable
    can_edit, can_comment = False, False
    if request.user.is_authenticated:
        member = get_object_or_404(Member, user_id=request.user)
        procedures = procedure_unit_conversion(member, procedures)
        can_edit = recipe_instance.owner_id == member
        can_comment = True
    reviews = Review.objects.filter(recipe_id=recipe_instance).order_by("-created")
    return render(
        request,
        "recipe_view_bootstrap.html",
        {
            "recipe": recipe_instance,
            "pk": pk,
            "can_edit": can_edit,
            "procedures": procedures,
            "can_comment": can_comment,
            "review_form": ReviewForm(),
            "reviews": reviews,
        },
    )


# model-formsets reference: https://docs.djangoproject.com/en/4.2/topics/forms/modelforms/#model-formsets
@login_required
def edit_recipe(request, pk):
    # The flow of this code would be a bit confusing,
    # the key is that we will go back to edit page and render despite whether
    # we save or not to ensure the integrity of data
    if request.method == "POST":
        recipe_form = RecipeForm(
            request.POST, request.FILES, instance=get_object_or_404(Recipe, pk=pk)
        )
        if recipe_form.is_valid():
            recipe_instance = recipe_form.save(commit=False)
            user_id = get_object_or_404(User, pk=request.user.id)
            cur_user = get_object_or_404(Member, user_id=user_id)
            # test ownership
            if recipe_instance.owner_id == cur_user:
                recipe_instance.save()
                # initalized form factories
                ProceduerFormSet = modelformset_factory(
                    Procedure, form=ProcedureForm, can_delete=True, extra=0
                )
                procedure_formset = ProceduerFormSet(request.POST)
                # check whether it's valid:
                if procedure_formset.is_valid():
                    procedures = procedure_formset.save(commit=False)
                    # delte on select, reference:https://docs.djangoproject.com/en/4.2/topics/forms/formsets/#dealing-with-ordering-and-deletion-of-forms
                    for obj in procedure_formset.deleted_objects:
                        obj.delete()
                    # save the extras and reorder
                    new_order = 0
                    for procedure in procedures:
                        new_order += 1
                        procedure.recipe_id = recipe_instance
                        procedure.order = new_order
                        procedure.save()
                    add_procedure_after_pk = request.POST.get("add_procedure", "")
                    if add_procedure_after_pk:
                        # redirect to edit after
                        add_procedure(request, pk, int(add_procedure_after_pk))
                    else:
                        messages.success(request, "recipe saved")
                        if request.POST.get("save_and_view", ""):
                            return redirect("recipes:get_recipe", pk=pk)
                else:
                    msg = ""
                    if procedure_formset.errors:
                        # render form errors:
                        msg += "invalid procedures: "
                        for dict in procedure_formset.errors:
                            for key, value in dict.items():
                                msg += key
                                for val in value:
                                    msg += val + ""
                                msg += "          "
                    if procedure_formset.non_form_errors():
                        msg += "Non form errors: " + procedure_formset.non_form_errors()
                    messages.error(request, msg)
            else:
                messages.error(request, "you don't have permission to edit this recipe")
        else:
            messages.error(request, "invalid recipe data")
        return redirect("recipes:edit_recipe", pk=pk)
    else:
        # test if recipe exist
        recipe_instance = get_object_or_404(Recipe, pk=pk)
        recipe_form = RecipeForm(instance=recipe_instance)
        # initalized form factories
        ProceduerFormSet = modelformset_factory(
            Procedure, form=ProcedureForm, can_delete=True, extra=0
        )
        # insert queries
        procedure_formsets = ProceduerFormSet(
            queryset=Procedure.objects.filter(recipe_id=recipe_instance).order_by(
                "order"
            )
        )
        # reset formset can_delete attribute
        for form in procedure_formsets:
            form.fields["DELETE"].widget.attrs["class"] = "form-check-input"
        return render(
            # Anchor function to be implement, js is not working
            request,
            "recipes_edit_bootstrap.html",
            {
                "recipe_form": recipe_form,
                "pk": pk,
                "procedure_formsets": procedure_formsets,
            },
        )


@login_required
def delete_recipe(request, pk):
    # only do post request:
    # since this form is really easy, I don't want to bother form class
    if request.method == "POST":
        recipe_instance = get_object_or_404(Recipe, pk=pk)
        # test ownership
        user_instance = get_object_or_404(User, pk=request.user.id)
        member_instance = get_object_or_404(Member, user_id=user_instance)
        if recipe_instance.owner_id == member_instance:
            recipe_name = recipe_instance.name
            if request.POST.get("doubleCheck") == recipe_name:
                recipe_instance.delete()
                messages.success(
                    request, f"Delete recipe {request.POST['doubleCheck']} success"
                )
                return redirect("recipes:index")
            else:
                messages.error(
                    request,
                    f"Recipe name mismatch with {recipe_name}, input found is: {request.POST.get('doubleCheck')}",
                )
        else:
            messages.error(request, "you don't have permission to edit this recipe")
    return redirect("recipes:edit_recipe", pk=pk)


# this article might be helpful: https://stackoverflow.com/questions/62962206/rendering-different-modelforms-based-on-dropdown-field
@login_required
def add_procedure(request, recipe_pk, add_procedure_after_pk):
    # backend processing only, special case for edit_recipe
    # test if recipe exist
    recipe_instance = get_object_or_404(Recipe, pk=recipe_pk)
    # test ownership
    user_instance = get_object_or_404(User, pk=request.user.id)
    member_instance = get_object_or_404(Member, user_id=user_instance)
    if recipe_instance.owner_id != member_instance:
        messages.error(request, "you don't have permission to edit this recipe")
        return redirect("recipes:get_recipe", pk=recipe_pk)
    procedures = Procedure.objects.filter(recipe_id=recipe_instance).order_by("order")
    # optimize can start from here from n to log(n), or even 1
    new_order, instance_order = 0, 0
    # add on frist
    if add_procedure_after_pk == 0:
        new_order += 1
        instance = Procedure.objects.create(
            recipe_id=recipe_instance,
            minutes_required=0.0,
            procedure_type=ProcedureTypeChoice.WAIT,
            order=new_order,
        )
        instance_order = new_order
        instance.save()
    for i in procedures:
        new_order += 1
        # when smaller, no change
        if i.pk < add_procedure_after_pk:
            continue
        # when greater, change order
        i.order = new_order
        i.save()
        # messages.info(request, f"searching.{i.pk},{add_procedure_after_pk}")
        if i.pk == add_procedure_after_pk:
            new_order += 1
            instance = Procedure.objects.create(
                recipe_id=recipe_instance,
                minutes_required=0.0,
                procedure_type=ProcedureTypeChoice.WAIT,
                order=new_order,
            )
            instance_order = new_order
            instance.save()
    return redirect("recipes:edit_recipe", pk=recipe_pk)


@login_required
def add_review(request, pk):
    if request.method == "POST":
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review_instance = review_form.save(commit=False)
            recipe_instance = get_object_or_404(Recipe, pk=pk)
            user_id = get_object_or_404(User, pk=request.user.id)
            member_instance = get_object_or_404(Member, user_id=user_id)
            review_instance.recipe_id = recipe_instance
            review_instance.sender_id = member_instance
            review_instance.save()
            messages.success(request, "add review success")
        else:
            messages.error(request, "review form invalid")
    return redirect("recipes:get_recipe", pk=pk)


# return the first index greater than order
def get_procedure(request, recipe_id, order):
    recipe_instance = get_object_or_404(Recipe, pk=recipe_id)
    procedure_instances = Procedure.objects.filter(recipe_id=recipe_instance).order_by(
        "order"
    )
    if request.user.is_authenticated:
        member = get_object_or_404(Member, user_id=request.user)
        procedure_instances = procedure_unit_conversion(member, procedure_instances)
    if len(procedure_instances) == 0:
        return render(
            request, "procedure_end_bootstrap.html", {"recipe": recipe_instance}
        )
    # tired of coding, just throw garbage to them if they don't follow
    if order >= len(procedure_instances):
        return render(
            request,
            "procedure_end_bootstrap.html",
            {"recipe": recipe_instance, "previous_order": len(procedure_instances) - 1},
        )
    # validify input
    order = max(0, order)
    # # binary search for order greater than
    # lo,hi=0,len(procedure_instances)-1
    # while lo<hi:
    #     mid=(lo+hi)>>1
    #     if procedure_instances[mid]<order:
    #         lo=mid+1
    #     else:
    #         hi=mid
    # cur_procedure=procedure_instances[lo]
    return render(
        request,
        "procedure_view_bootstrap.html",
        {
            "recipe": recipe_instance,
            "procedure": procedure_instances[order],
            "cur_order": order,
        },
    )


def search_recipe(request):
    query = request.POST.get("query", "")
    # keywords should store in get, no post request accepted.
    recipes_query = Recipe.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ).order_by("-created")
    return render(
        request,
        "recipes_list_bootstrap.html",
        {"recipes": recipes_query, "query": query, "on_search": True},
    )


def procedure_unit_conversion(member, procedures):
    for procedure in procedures:
        if procedure.amount:
            procedure.amount = (
                ceil(
                    UnitMassChoices.Convert(
                        UnitMassChoices,
                        float(procedure.amount),
                        procedure.unit_mass,
                        member.unit_mass,
                    )
                    * 100
                )
                / 100
            )
            procedure.unit_mass = member.unit_mass
        if procedure.temperature:
            procedure.temperature = (
                ceil(
                    UnitTempChoices.Convert(
                        UnitTempChoices,
                        float(procedure.temperature),
                        procedure.unit_temperature,
                        member.unit_temperature,
                    )
                    * 100
                )
                / 100
            )
            procedure.unit_temperature = member.unit_temperature
        if procedure.size:
            procedure.size = (
                ceil(
                    UnitLengthChoices.Convert(
                        UnitLengthChoices,
                        float(procedure.size),
                        procedure.unit_size,
                        member.unit_size,
                    )
                    * 100
                )
                / 100
            )
            procedure.unit_size = member.unit_size
    return procedures
