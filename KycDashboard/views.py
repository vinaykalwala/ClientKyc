from django.shortcuts import render

def Home(requests):
    return render(requests, 'index.html')