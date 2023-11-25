"""
Place to set up database

After you modified these files, please remember to make migrations

1. run the following command
python manage.py makemigrations members
python manage.py migrate 
python manage.py runserver

2. If you modified the table too much, it is really easy to get errors,
please save the origional database and edit for postgre
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# unit preferences reference: https://docs.djangoproject.com/en/4.2/ref/models/fields/
class UnitMassChoices(models.TextChoices):
    GRAM = "G", _("Grams")
    OUNCE = "O", _("Ounce")

    def Convert(self,value,unita,unitb):
        # convert everything to gram
        if unita==self.OUNCE:
            value*=28.34952
        # converting form gram
        if unitb==self.OUNCE:
            value/=28.34952
        return value

class UnitLengthChoices(models.TextChoices):
    INCH = "I", _("Inch")
    CENTIMETER = "C", _("Centimeter")
    
    def Convert(self,value,unita,unitb):
        # convert everything to centimeter
        if unita==self.INCH:
            value*=2.54
        # converting form gram
        if unitb==self.INCH:
            value/=2.54
        return value

class UnitTempChoices(models.TextChoices):
    CELSIUS = "C", _("Celsius")
    FAHRENHEIT = "F", _("Fahrenheit")
    KELVIN = "K", _("Kelvin")

    def Convert(self,value,unita,unitb):
        # convert everything to kelvin
        if unita==self.CELSIUS:
            value+=273.15
        elif unita==self.FAHRENHEIT:
            value=value/1.8+255.372
        # converting form kelvin
        if unitb==self.CELSIUS:
            value-=273.15
        elif unitb==self.FAHRENHEIT:
            value=(value-255.372)*1.8
        return value

class Member(models.Model):
    # for django built-in authentication: https://docs.djangoproject.com/en/4.2/ref/contrib/auth/
    # This objects contains the username, password, first_name, last_name, and email of member.
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # when member is delete, user would also be deleted
        on_delete=models.CASCADE,
        null=False
    )
    motto = models.CharField(max_length=100,null=True)
    reputation = models.IntegerField(default=0,null=False)
    exp = models.IntegerField(default=0,null=False)
    social_link = models.URLField(max_length=255, null=True)

    # last_login and date_joined automatically created by user_id

    unit_mass = models.CharField(
        null=False, max_length=1, choices=UnitMassChoices.choices, default=UnitMassChoices.GRAM
    )

    unit_temperature = models.CharField(
        null=False,
        max_length=1,
        choices=UnitTempChoices.choices,
        default=UnitTempChoices.CELSIUS,
    )
    
    unit_size = models.CharField(
        null=False, max_length=1, choices=UnitLengthChoices.choices, default=UnitLengthChoices.CENTIMETER
    )

    # user status is detemined by the group in user attribute

    # for better list display
    def __str__(self):
        return f"{self.user_id.get_full_name()}"
