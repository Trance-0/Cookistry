import collections
from django.db import models
from members.models import Member, UnitMassChoices, UnitTempChoices, UnitLengthChoices
from django.utils.translation import gettext_lazy as _


# Create your models here.
class Recipe(models.Model):
    name = models.CharField(null=False, max_length=100, default="Mysterious recipe")
    owner_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    picture = models.ImageField(null=True, blank=True)
    description = models.CharField(max_length=1000)
    safety_notes = models.CharField(max_length=1000)
    total_views = models.IntegerField(null=False, default=0)
    created = models.DateTimeField(null=False, auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} {self.owner_id.user_id.username}"

    def estimate_time(self) -> float:
        return sum(
            [i.minutes_required for i in Procedure.objects.filter(recipe_id=self)]
        )

    def ingredients_list(self) -> list:
        # for each ingredient, we only pick the mas amount
        ingredient_dict = collections.defaultdict(list)
        for i in Procedure.objects.filter(recipe_id=self).order_by("-amount"):
            if ingredient_dict[i.ingredient]:
                continue
            ingredient_dict[i.ingredient] = (i.amount, i.unit_mass)
        return [(key, value[0], value[1]) for key, value in ingredient_dict.items()]

    def cookware_list(self) -> list:
        return [
            i.cookware
            for i in Procedure.objects.filter(recipe_id=self).distinct()
            if "cookware" not in i.cookware
        ]

    def score(self) -> float:
        reviews = Review.objects.filter(recipe_id=self)
        return None if len(reviews)==0 else sum([i.score for i in reviews]) / len(reviews)

    def reviews_list(self) -> list:
        # to be implement
        return []


class ProcedureTypeChoice(models.TextChoices):
    ADD = "A", _("add ingredient")
    HEAT = "H", _("heat ingredient")
    CUT = "C", _("cut ingredient")
    WAIT = "W", _("wait until")


# I know it sounds fancy to use inheritence, but it just be very hard to keep track of the form, so we use validation for each type of input instead.
class Procedure(models.Model):
    recipe_id = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    minutes_required = models.DecimalField(
        null=False, max_digits=4, decimal_places=1, default=0
    )
    # this field is to set additional treatment to the cookware like setting the mode for HEAT
    notes = models.CharField(null=True, max_length=1000)
    order = models.IntegerField(null=False, default=0)
    # Optional for every procedure actually, when you are not sure when to stop
    end_condition = models.CharField(null=True, max_length=1000, default="Timer ends")
    # validation base on procedure type, a little bit complex but easier to manage
    procedure_type = models.CharField(
        null=False,
        max_length=1,
        choices=ProcedureTypeChoice.choices,
        default=ProcedureTypeChoice.WAIT,
    )
    # Required for: ADD, CUT, HEAT
    ingredient = models.CharField(null=True, max_length=100, default="Air")
    # Required for: ADD, CUT, HEAT
    cookware = models.CharField(null=True, max_length=100, default="Previous cookware")
    # Required for: ADD
    amount = models.DecimalField(null=True, max_digits=8, decimal_places=4, default=0)
    unit_mass = models.CharField(
        null=True,
        max_length=1,
        choices=UnitMassChoices.choices,
        default=UnitMassChoices.GRAM,
    )
    # Optional for HEAT
    temperature = models.DecimalField(
        null=True, max_digits=4, decimal_places=1, default=0
    )
    unit_temperature = models.CharField(
        null=True,
        max_length=1,
        choices=UnitTempChoices.choices,
        default=UnitTempChoices.CELSIUS,
    )
    # Required for CUT
    size = models.DecimalField(null=True, max_digits=4, decimal_places=2, default=1)
    unit_size = models.CharField(
        null=True,
        max_length=1,
        choices=UnitLengthChoices.choices,
        default=UnitLengthChoices.CENTIMETER,
    )

    def __str__(self) -> str:
        return f"{self.recipe_id.name}-{self.order}-{self.procedure_type}"

    # render given recipe
    def as_card(self) -> str:
        card_html = f"""
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">Step {self.order}</h5>
                <h6 class="card-subtitle mb-2 text-body-secondary">Estimate time: {self.minutes_required} min</h6>
                <div class="card-text">
        """
        if self.procedure_type == ProcedureTypeChoice.ADD:
            card_html += f"""
                    <p class="card-text"><strong>Add</strong>
                     {self.ingredient}: {self.amount} {self.get_unit_mass_display()} to {self.cookware}</p>
            """
        elif self.procedure_type == ProcedureTypeChoice.HEAT:
            card_html += f"""
                    <p class="card-text"><strong>Heat</strong>
                     {self.ingredient} using {self.cookware} to {self.temperature} {self.get_unit_temperature_display()}</p>
            """
        elif self.procedure_type == ProcedureTypeChoice.CUT:
            card_html += f"""
                    <p class="card-text"><strong>Cut</strong>
                     {self.ingredient} using {self.cookware} to {self.size} {self.get_unit_size_display()}</p>
            """
        else:
            card_html += f"""
                    <p class="card-text"><strong>Wait</strong>
                    until {self.end_condition}</p>    
            """
        card_html += "</div>"
        card_html+=f"""
                    <p class="card-text">
                        {self.notes}
                    </p>    
                </div>
            </div>
        """
        return card_html

class ScoreChoice(models.IntegerChoices):
    CRITICAL_PERFECT = 5, _("Best")
    PERFECT = 4, _("Perfect")
    GREAT = 3, _("Great")
    GOOD = 2, _("Good")
    MISS = 1, _("Bad")


class Review(models.Model):
    recipe_id = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    score = models.IntegerField(
        null=False, choices=ScoreChoice.choices, default=ScoreChoice.PERFECT
    )
    content = models.CharField(max_length=1000)
    sender_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    created = models.DateTimeField(null=False, auto_now=True)

    def __str__(self) -> str:
        return f"{self.sender_id.user_id.username} {self.score}"

    def as_card(self) -> str:
        card_html = f"""
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">{self.sender_id.user_id.username}</h5>
                <h6 class="card-subtitle mb-2 text-body-secondary">Rating: {self.score}</h6>
                <div class="card-text">
                {self.content}
                </div>
            </div>
            <div class="card-footer">
                {self.created}
            </div>
        </div>
        """
        return card_html
