from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import get_user_model
from game.models import Game

User = get_user_model()

# 1. 전체 랭킹 리그 화면
def ranking_view(request):
    # accounts의 Profile 점수 순으로 내림차순 정렬
    ranking_list = User.objects.all().order_by('-score')
    return render(request, 'ranking.html', {'ranking_list': ranking_list})


# 2. 나의 전적 조회 화면
@login_required
def record_view(request):
    user = request.user
    
    # 1. 로그인한 유저가 공격자(attacker)이거나 방어자(defender)인 모든 게임을 조회
    all_my_games = Game.objects.filter(
        Q(attacker=user) | Q(defender=user)
    ).order_by('-created_at') # 최신 게임 순 정렬 (필드명에 따라 -id 등으로 변경 가능)
    
    wins = 0
    losses = 0
    draws = 0
    
    # 템플릿에서 편리하게 상태를 구별하여 렌더링하기 위해 가공 데이터를 담을 리스트
    processed_games = []
    
    for game in all_my_games:
        # 기본 매치 정보를 딕셔너리로 세팅
        game_data = {
            'id': game.id,
            'attacker': game.attacker,
            'defender': game.defender,
            'status': game.status, # 'completed', 'ongoing' 등 모델 스펙에 맞춤
            'display_status': '',  # 템플릿 분기용 태그
        }
        
        # A. 종료된 게임인 경우 -> 승/무/패 판정 및 통계 계산
        if game.status == 'completed':
            if game.result == 'draw':
                draws += 1
                game_data['display_status'] = 'draw'
            elif (game.attacker == user and game.result == 'attacker') or (game.defender == user and game.result == 'defender'):
                wins += 1
                game_data['display_status'] = 'win'
            else:
                losses += 1
                game_data['display_status'] = 'lose'
                
        # B. 아직 진행 중인 게임인 경우 (status가 'completed'가 아닌 경우)
        else:
            # 내가 공격한 게임인데 상대가 아직 반격하지 않은 경우 -> [진행중..] 및 [게임취소] 활성화
            if game.attacker == user:
                game_data['display_status'] = 'my_attack_ongoing'
            # 다른 유저가 나에게 게임을 신청하여 내가 반격해야 하는 경우 -> [CounterAttack] 활성화
            elif game.defender == user:
                game_data['display_status'] = 'need_counter'
                
        processed_games.append(game_data)
            
    total_games = wins + losses + draws
    win_rate = round((wins / total_games) * 100, 1) if total_games > 0 else 0
    
    context = {
        'games': processed_games, # 가공된 대결 리스트 전달
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'total_games': total_games,
        'win_rate': win_rate,
    }
    return render(request, 'record.html', context)