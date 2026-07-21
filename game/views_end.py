
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Game, deal_hand

SESSION_KEY_PREFIX = "defender_hand_"  # 게임별로 손패를 따로 저장


@login_required
def counter_page(request, game_id):
    """반격하기 페이지: 나(defender)에게 온 특정 공격 신청에 랜덤 카드 5장 제시."""
    game = get_object_or_404(
        Game, pk=game_id, defender=request.user, status=Game.Status.WAITING
    )

    session_key = f"{SESSION_KEY_PREFIX}{game.id}"
    hand = request.session.get(session_key)
    if not hand:
        hand = deal_hand()
        request.session[session_key] = hand

    return render(request, "game/counter.html", {"game": game, "hand": hand})


@login_required
@require_POST
def submit_counter(request, game_id):
    """반격 카드 제출 → Game.resolve()가 승패 판정 + 점수 반영 + 종료 처리까지 담당."""
    game = get_object_or_404(
        Game, pk=game_id, defender=request.user, status=Game.Status.WAITING
    )

    hand = request.session.get(f"{SESSION_KEY_PREFIX}{game.id}")
    card = request.POST.get("card")

    if not hand or not card:
        messages.error(request, "카드를 선택해주세요.")
        return redirect("game:counter_page", game_id=game.id)

    try:
        card = int(card)
    except (TypeError, ValueError):
        messages.error(request, "잘못된 카드 값입니다.")
        return redirect("game:counter_page", game_id=game.id)

    if card not in hand:
        messages.error(request, "제시된 카드 중에서만 선택할 수 있어요. 다시 시도해주세요.")
        return redirect("game:counter_page", game_id=game.id)

    game.resolve(card)  # 승패 판정 + 점수 F식 반영 + status=FINISHED 처리까지 모델이 담당
    request.session.pop(f"{SESSION_KEY_PREFIX}{game.id}", None)

    return redirect("game:detail", game_id=game.id)


@login_required
def game_detail(request, game_id):
    """게임 결과 표시 페이지. attacker/defender 둘 다 볼 수 있음."""
    game = get_object_or_404(Game, pk=game_id)

    if request.user not in (game.attacker, game.defender):
        messages.error(request, "본인이 참여한 게임만 볼 수 있어요.")
        return redirect("game:attack")  # 시작 담당이 만든 페이지로 이동

    return render(request, "game/detail.html", {"game": game})