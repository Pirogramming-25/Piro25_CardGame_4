from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Game, deal_hand

User = get_user_model()

# 공격 페이지에서 제공한 5장의 손패를 세션에 보관하는 키.
# 제출된 카드가 실제로 제공된 5장 중 하나인지 검증하는 데 사용한다.
SESSION_HAND_KEY = "attack_hand"


@login_required
def attack(request):
    """공격하기 페이지.

    - GET: 랜덤 카드 5장, 대결 상대 목록, 내가 보낸 대기중 신청을 보여준다.
    - POST: 선택한 카드/상대로 공격 신청(Game)을 생성한다.
    """
    if request.method == "POST":
        return _create_attack(request)

    # 1~10 중 서로 다른 5장을 뽑아 세션에 저장(제출 시 검증에 사용).
    hand = deal_hand()
    request.session[SESSION_HAND_KEY] = hand

    opponents = User.objects.exclude(pk=request.user.pk).order_by("username")
    my_pending = Game.objects.filter(
        attacker=request.user, status=Game.Status.WAITING
    ).select_related("defender")

    context = {
        "hand": hand,
        "opponents": opponents,
        "my_pending": my_pending,
    }
    return render(request, "game/attack.html", context)


def _create_attack(request):
    """공격 신청 생성 처리."""
    hand = request.session.get(SESSION_HAND_KEY)

    try:
        card = int(request.POST.get("card", ""))
    except (TypeError, ValueError):
        card = None

    # 제출한 카드는 반드시 이번에 제공된 5장 중 하나여야 한다.
    if not hand or card not in hand:
        messages.error(request, "제공된 카드 중에서 선택해주세요.")
        return redirect("game:attack")

    # 상대는 유효한 사용자여야 하며, 자기 자신은 선택할 수 없다.
    opponent = (
        User.objects.exclude(pk=request.user.pk)
        .filter(pk=request.POST.get("opponent"))
        .first()
    )
    if opponent is None:
        messages.error(request, "대결할 상대를 선택해주세요.")
        return redirect("game:attack")

    Game.objects.create(
        attacker=request.user,
        defender=opponent,
        attacker_card=card,
    )
    request.session.pop(SESSION_HAND_KEY, None)  # 사용한 손패 정리
    messages.success(request, f"{opponent.username} 님에게 대결을 신청했습니다!")
    return redirect("game:attack")


@login_required
@require_POST
def cancel_attack(request, pk):
    """내가 보낸 신청을 상대가 반격하기 전(WAITING)까지 취소(삭제)한다.

    (요구사항 8) 공격자 본인의 신청만, 아직 반격되지 않은 경우에만 취소 가능.
    """
    game = get_object_or_404(Game, pk=pk, attacker=request.user)
    if not game.can_be_deleted:
        messages.error(request, "이미 반격이 진행되어 취소할 수 없습니다.")
        return redirect("game:attack")

    game.delete()
    messages.success(request, "신청을 취소했습니다.")
    return redirect("game:attack")
