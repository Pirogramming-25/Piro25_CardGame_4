
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """서비스 사용자."""
    score = models.IntegerField(
        default=0,
        help_text="게임 승패로 누적되는 점수. 랭킹 정렬 기준.",
    )

    class Meta:
        ordering = ["-score", "username"]

    def __str__(self):
        return f"{self.username} ({self.score}점)"