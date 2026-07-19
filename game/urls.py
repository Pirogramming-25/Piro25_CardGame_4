from django.urls import path

from . import views_start

app_name = "game"

urlpatterns = [
    # 시작 담당: 공격하기 페이지 / 신청 생성 / 신청 취소
    path("attack/", views_start.attack, name="attack"),
    path("attack/<int:pk>/cancel/", views_start.cancel_attack, name="cancel_attack"),
    # 끝 담당(views_end): 반격하기 / 게임 detail 등은 여기에 추가
]
