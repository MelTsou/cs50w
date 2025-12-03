from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from encryptedmessenger.models import User


@ensure_csrf_cookie
def index(request):
    if request.user.is_authenticated:
        return render(request, "encryptedmessenger/index.html")
    return HttpResponseRedirect(reverse("login"))


def login_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "encryptedmessenger/login.html",{
                "message": "Username and/or Password are not valid."
            })
    else:
        return render(request, "encryptedmessenger/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register_view(request):
    if request.method =="POST":
        username = request.POST["username"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "encryptedmessenger/register.html", {
                "message": "'Password' and 'Confirm Password' must match."
            })

        try:
            user = User.objects.create_user(username=username, password=password)
            user.save()
        except IntegrityError:
            return render(request, "encryptedmessenger/register.html", {
                "message": "Username already exists."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "encryptedmessenger/register.html")
