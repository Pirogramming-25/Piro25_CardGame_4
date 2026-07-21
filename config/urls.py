"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from history import views


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
    path("record/", views.record_view, name="record"),
    path("ranking/", views.ranking_view, name="ranking"),
]