"""
Admin view registration

After you modify the class, don't forget to register the models or 
they will not be avaliable in admin site.
"""

from django.contrib import admin

# Register your models here.
from .models import Member

# Set up display methods
class MemberInline(admin.StackedInline):
    model=Member
    extra=1

# Add model to admin view
admin.site.register(Member)