from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """서비스 사용자.

    기본 인증 기능(username/password 등)은 ``AbstractUser`` 를 그대로 사용하고,
    게임 결과로 누적되는 점수(``score``)를 추가한다. 랭킹 리그(7번 요구사항)는
    이 ``score`` 를 기준으로 정렬해 보여준다.
    """

    score = models.IntegerField(
        default=0,
        help_text="게임 승패로 누적되는 점수. 랭킹 정렬 기준.",
    )

    class Meta:
        ordering = ["-score", "username"]

    def __str__(self):
        return f"{self.username} ({self.score}점)"
