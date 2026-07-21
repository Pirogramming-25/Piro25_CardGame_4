from game.models import Game

def pending_counter_context(request):
    if request.user.is_authenticated:
        # 내가 방어자(defender)이고 아직 반격 대기 중(WAITING)인 게임 수 카운트
        count = Game.objects.filter(
            defender=request.user,
            status=Game.Status.WAITING
        ).count()
        return {'pending_counter_count': count}
    return {'pending_counter_count': 0}