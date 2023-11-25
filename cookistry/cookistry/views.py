"""
This is where you handle requests (front-end)
Also, you can modify models here (back-end)
"""

from django.shortcuts import render

def home(request):
    return render()

def about(request):
    return render(request,'about.html',{})