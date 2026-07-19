from django.db import models

from game.models import Game


class FinishedGameManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Game.Status.FINISHED)


class GameHistory(Game):
    """종료된 게임만 다루는 프록시 모델.

    실제 데이터는 ``game.Game`` 과 동일한 테이블을 공유하며(별도 저장 없음),
    히스토리/전적 화면에서 종료된 대결만 조회할 때 사용한다.
    """

    objects = FinishedGameManager()

    class Meta:
        proxy = True
        verbose_name = "게임 기록"
        verbose_name_plural = "게임 기록"
