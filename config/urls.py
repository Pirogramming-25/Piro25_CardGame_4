"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def coming_soon(request):
    return HttpResponse("<h1>준비중</h1>")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("accounts.urls")),
    path("game/", include("game.urls")),
    path("history/", include("history.urls")),
]

urlpatterns += [
    path("games/", coming_soon, name="game_list"),
    path("ranking/", coming_soon, name="ranking"),
]