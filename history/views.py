from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import get_user_model
from game.models import Game

User = get_user_model()

# 1. 전체 랭킹 리그 화면
def ranking_view(request):
    # accounts의 Profile 점수 순으로 내림차순 정렬
    rankings = User.objects.all()
    return render(request, 'ranking.html', {'rankings': rankings})


# 2. 나의 전적 조회 화면
@login_required
def record_view(request):
    user = request.user
    
    # game 앱의 Game 모델에서 완료된 대결들만 조회
    completed_games = Game.objects.filter(
        (Q(attacker=user) | Q(defender=user)) & Q(status='completed')
    ).order_by('-completed_at')
    
    wins = 0
    losses = 0
    draws = 0
    
    for game in completed_games:
        if game.result == 'draw':
            draws += 1
        elif (game.attacker == user and game.result == 'attacker') or (game.defender == user and game.result == 'defender'):
            wins += 1
        else:
            losses += 1
            
    total_games = wins + losses + draws
    win_rate = round((wins / total_games) * 100, 1) if total_games > 0 else 0
    
    context = {
        'games': completed_games,
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'total_games': total_games,
        'win_rate': win_rate,
    }
    return render(request, 'record.html', context)