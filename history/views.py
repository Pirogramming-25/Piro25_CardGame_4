from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import get_user_model
from game.models import Game

User = get_user_model()


# 1. 전체 랭킹 리그 화면
def ranking_view(request):
    # 전체 순위 (점수 내림차순)
    ranking_list = User.objects.all().order_by('-score')
    
    # 1~3위 (PODIUM용)
    top3 = list(ranking_list[:3])
    
    podium_list = []
    if len(top3) >= 2:
        podium_list.append({'user': top3[1], 'rank': 2, 'class': 'rank-2'}) # 2위 (좌)
    if len(top3) >= 1:
        podium_list.append({'user': top3[0], 'rank': 1, 'class': 'rank-1'}) # 1위 (중앙)
    if len(top3) >= 3:
        podium_list.append({'user': top3[2], 'rank': 3, 'class': 'rank-3'}) # 3위 (우)
        
    # 4위부터 나머지 목록
    other_rankings = ranking_list[3:]

    context = {
        'podium_list': podium_list,
        'other_rankings': other_rankings,
    }
    return render(request, 'ranking.html', context)

# 2. 나의 전적 조회 화면
@login_required
def record_view(request):
    user = request.user
    
    # 로그인한 유저가 공격자(attacker)이거나 방어자(defender)인 모든 게임 조회
    all_my_games = Game.objects.filter(
        Q(attacker=user) | Q(defender=user)
    ).order_by('-id')  # 최신 생성 순 정렬
    
    wins = 0
    losses = 0
    draws = 0
    
    processed_games = []
    
    for game in all_my_games:
        game_data = {
            'id': game.id,
            'attacker': game.attacker,
            'defender': game.defender,
            'status': game.status,
            'display_status': '',
        }
        
        # A. 게임이 종료된 경우 (Game.Status.FINISHED)
        if game.status == Game.Status.FINISHED:
            # 1) winner 필드가 있는 모델 구조인 경우
            if hasattr(game, 'winner'):
                if game.winner is None:
                    draws += 1
                    game_data['display_status'] = 'draw'
                elif game.winner == user:
                    wins += 1
                    game_data['display_status'] = 'win'
                else:
                    losses += 1
                    game_data['display_status'] = 'lose'
            # 2) result 문자열 필드를 사용하는 모델 구조인 경우 ('draw', 'attacker_win' 등)
            else:
                if game.result == 'draw':
                    draws += 1
                    game_data['display_status'] = 'draw'
                elif (game.attacker == user and 'attacker' in str(game.result)) or \
                     (game.defender == user and 'defender' in str(game.result)):
                    wins += 1
                    game_data['display_status'] = 'win'
                else:
                    losses += 1
                    game_data['display_status'] = 'lose'

        # B. 게임이 진행/대기 중인 경우 (Game.Status.WAITING)
        else:
            # 내가 공격하고 상대의 반격을 기다리는 중 -> [진행 중..] & [게임취소]
            if game.attacker == user:
                game_data['display_status'] = 'my_attack_ongoing'
            # 상대가 나를 공격해서 내가 반격해야 하는 경우 -> [CounterAttack]
            elif game.defender == user:
                game_data['display_status'] = 'need_counter'
                
        processed_games.append(game_data)
            
    total_games = wins + losses + draws
    win_rate = round((wins / total_games) * 100, 1) if total_games > 0 else 0
    
    context = {
        'games': processed_games,
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'total_games': total_games,
        'win_rate': win_rate,
    }
    return render(request, 'record.html', context)