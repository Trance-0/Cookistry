"""
Escape from forms

With django built-in validation and everything else!
https://docs.djangoproject.com/en/4.2/topics/forms/
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Recipe, Procedure, Review
from members.models import UnitTempChoices


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ["name", "picture", "description", "safety_notes"]
        labels = {
            "name": _("Recipe name"),
            "picture": _("Add a tasty picture to lure your viewers"),
        }
        help_texts = {
            "description": _(
                "This should be the main reason that why you make this dish."
            ),
            "safety_notes": _("Cooking is like chemistry, but you can lick the spoon!"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "safety_notes": forms.Textarea(attrs={"rows": 3}),
        }

    # add extra arguments for each input, reference: https://stackoverflow.com/questions/29716023/add-class-to-form-field-django-modelform
    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


# I just guess that the procedure form will not work because it is an abstract class.
class ProcedureForm(forms.ModelForm):
    # set visibility of each field by js
    class Meta:
        model = Procedure
        fields = [
            "minutes_required",
            "end_condition",
            "notes",
            "procedure_type",
            "amount",
            "unit_mass",
            "temperature",
            "unit_temperature",
            "size",
            "unit_size",
            "ingredient",
            "cookware",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    # add extra arguments for each input, reference: https://stackoverflow.com/questions/29716023/add-class-to-form-field-django-modelform
    def __init__(self, *args, **kwargs):
        super(ProcedureForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            if visible.name == "procedure_type":
                # post on select reference: https://stackoverflow.com/questions/4934839/django-post-form-on-select
                visible.field.widget.attrs["onchange"] = "this.form.submit();"

        # set note require to false:
        self.fields["notes"].required = False

        def setstate(value):
            optional_field_name = [
                "amount",
                "unit_mass",
                "temperature",
                "unit_temperature",
                "size",
                "unit_size",
                "ingredient",
                "cookware",
            ]
            for i in optional_field_name:
                if value & 1:
                    del self.fields[i]
                value >>= 1

        if self.instance:
            # conditional field rendering reference: https://stackoverflow.com/questions/49500316/python-django-modelform-how-can-i-modify-a-form-fields-before-rendering-it-depe
            if self.instance.procedure_type == "A":
                setstate(0b00111100)
            elif self.instance.procedure_type == "H":
                setstate(0b11001100)
            elif self.instance.procedure_type == "C":
                setstate(0b11110000)
            else:
                setstate(0b11111111)
        # default setting is wait
        else:
            # here are all the optional values, lol
            setstate(0b11111111)

    # customize cleaning reference:https://docs.djangoproject.com/en/4.2/topics/forms/formsets/#custom-formset-validation
    def clean(self):
        # warning: do not call form instance, that is the one saved on sql!
        if any(self.errors):
            return
        # bypass validation if procedure type changed reference:https://docs.djangoproject.com/en/4.2/ref/forms/api/#django.forms.Form.has_changed
        if "procedure_type" in self.changed_data:
            return
        # cleaning reference: https://stackoverflow.com/questions/12278753/clean-method-in-model-and-field-validation
        # you should access cleaning data rather than the fields value.
        data = self.cleaned_data
        if data["minutes_required"] < 0:
            raise ValidationError(
                _("This website do include the concept of time and we define that as non-negative values")
            )
        # configuring required field
        if data["procedure_type"] == "A" and (
            data["amount"] <= 0 or data["unit_mass"] == None
        ):
            raise ValidationError("Invalid Add value")
        elif data["procedure_type"] == "H" and (
            data["unit_temperature"] == None
            or UnitTempChoices.Convert(
                UnitTempChoices,
                float(data["temperature"]),
                data["unit_temperature"],
                UnitTempChoices.KELVIN,
            )
            < 0
        ):
            raise ValidationError(
                _("Invalid Heat value"
                + str(
                    UnitTempChoices.Convert(
                        UnitTempChoices,
                        float(data["temperature"]),
                        data["unit_temperature"],
                        UnitTempChoices.KELVIN,
                    )
                ))
            )
        elif data["procedure_type"] == "C" and (
            data["size"] <= 0 or data["unit_size"] == None
        ):
            raise ValidationError(_("Invalid Cut value"))


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        exclude = ["recipe_id", "sender_id"]
        widgets = {"content": forms.Textarea(attrs={"rows": 3})}
    # add extra arguments for each input, reference: https://stackoverflow.com/questions/29716023/add-class-to-form-field-django-modelform
    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"