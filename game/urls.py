from django.urls import path

from . import views_start, views_end

app_name = "game"

urlpatterns = [
    # 시작 담당: 공격하기 페이지 / 신청 생성 / 신청 취소
    path("attack/", views_start.attack, name="attack"),
    path("attack/<int:pk>/cancel/", views_start.cancel_attack, name="cancel_attack"),
    path("<int:game_id>/counter/", views_end.counter_page, name="counter_page"),
    path("<int:game_id>/counter/submit/", views_end.submit_counter, name="submit_counter"),
    path("<int:game_id>/", views_end.game_detail, name="detail"),

]
