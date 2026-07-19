import random

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone

# 숫자 카드 범위와 한 번에 제공되는 카드 수
CARD_MIN = 1
CARD_MAX = 10
HAND_SIZE = 5


def deal_hand():
    """1~10 중 서로 다른 숫자 카드 ``HAND_SIZE`` 장을 뽑아 반환한다.

    사용자에게 제시할 손패를 만들 때 사용한다(뷰에서 호출). 사용자는 이 중
    한 장을 골라 제출한다.
    """
    return random.sample(range(CARD_MIN, CARD_MAX + 1), HAND_SIZE)


class Game(models.Model):
    """두 사용자 간의 숫자 카드 대결.

    - 공격자(attacker)가 카드를 골라 방어자(defender)에게 대결을 신청하면
      ``WAITING`` 상태의 Game 이 생성된다.
    - 방어자가 반격 카드를 제출하면 ``resolve()`` 가 호출되어 승패와 점수가
      확정되고 상태가 ``FINISHED`` 로 바뀐다.
    - 방어자가 반격하기 전(``WAITING``)까지는 공격자가 신청을 삭제할 수 있다.
    """

    class Status(models.TextChoices):
        WAITING = "waiting", "반격 대기"
        FINISHED = "finished", "종료"

    class Rule(models.TextChoices):
        HIGH = "high", "큰 숫자 승리"
        LOW = "low", "작은 숫자 승리"

    class Result(models.TextChoices):
        ATTACKER_WIN = "attacker_win", "공격자 승"
        DEFENDER_WIN = "defender_win", "방어자 승"
        DRAW = "draw", "무승부"

    attacker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_attacking",
        verbose_name="공격자",
    )
    defender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_defending",
        verbose_name="방어자",
    )

    attacker_card = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(CARD_MIN), MaxValueValidator(CARD_MAX)],
        verbose_name="공격자 카드",
    )
    defender_card = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(CARD_MIN), MaxValueValidator(CARD_MAX)],
        verbose_name="방어자 카드",
        help_text="방어자가 반격하기 전에는 비어 있다.",
    )

    # 승패 기준(큰 수/작은 수 승리)은 결과 확정 시점에 랜덤으로 정해진다.
    rule = models.CharField(
        max_length=10,
        choices=Rule.choices,
        blank=True,
        verbose_name="승리 기준",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WAITING,
        verbose_name="상태",
    )
    result = models.CharField(
        max_length=12,
        choices=Result.choices,
        blank=True,
        verbose_name="결과",
    )

    # 이 게임으로 각자의 점수가 얼마나 변했는지 기록(기록/랭킹 검증용).
    attacker_delta = models.IntegerField(default=0, verbose_name="공격자 점수 변동")
    defender_delta = models.IntegerField(default=0, verbose_name="방어자 점수 변동")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="신청 시각")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="종료 시각")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(attacker=models.F("defender")),
                name="game_attacker_ne_defender",
            ),
        ]

    def __str__(self):
        return f"{self.attacker} → {self.defender} ({self.get_status_display()})"

    @property
    def is_waiting(self):
        return self.status == self.Status.WAITING

    @property
    def can_be_deleted(self):
        """공격자는 반격 전(WAITING)까지만 신청을 삭제할 수 있다(8번 요구사항)."""
        return self.status == self.Status.WAITING

    @property
    def winner(self):
        if self.result == self.Result.ATTACKER_WIN:
            return self.attacker
        if self.result == self.Result.DEFENDER_WIN:
            return self.defender
        return None

    @transaction.atomic
    def resolve(self, defender_card):
        """방어자의 카드로 승패와 점수를 확정한다.

        - 승리 기준(큰 수/작은 수)은 이 시점에 랜덤으로 결정된다.
        - 승자는 자신의 카드 숫자만큼 점수를 얻고, 패자는 자신의 카드 숫자만큼
          점수를 잃는다. 무승부면 변동 없음.
        """
        if self.status != self.Status.WAITING:
            raise ValueError("이미 종료된 게임입니다.")

        self.defender_card = defender_card
        self.rule = random.choice([self.Rule.HIGH, self.Rule.LOW])

        a, d = self.attacker_card, self.defender_card
        if a == d:
            self.result = self.Result.DRAW
            self.attacker_delta = 0
            self.defender_delta = 0
        else:
            if self.rule == self.Rule.HIGH:
                attacker_wins = a > d
            else:
                attacker_wins = a < d

            if attacker_wins:
                self.result = self.Result.ATTACKER_WIN
                self.attacker_delta = a
                self.defender_delta = -d
            else:
                self.result = self.Result.DEFENDER_WIN
                self.attacker_delta = -a
                self.defender_delta = d

        # 사용자 누적 점수에 반영 (경합 방지를 위해 F 표현식 사용)
        User = self.attacker.__class__
        if self.attacker_delta:
            User.objects.filter(pk=self.attacker_id).update(
                score=models.F("score") + self.attacker_delta
            )
        if self.defender_delta:
            User.objects.filter(pk=self.defender_id).update(
                score=models.F("score") + self.defender_delta
            )

        self.status = self.Status.FINISHED
        self.finished_at = timezone.now()
        self.save()
        return self.result
