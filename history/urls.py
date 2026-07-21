from django.urls import path
from . import views

app_name = 'history'

urlpatterns = [
    path('ranking/', views.ranking_view, name='ranking'),    # 전체 랭킹 페이지
    path('record/', views.record_view, name='record'),       # 나의 전적 페이지
]