from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import HAND_SIZE, Game
from .views_start import SESSION_HAND_KEY, _get_or_deal_hand

User = get_user_model()


class DealHandSessionTests(SimpleTestCase):
    """새로고침(GET 반복)으로 카드를 다시 뽑는 리롤이 불가능한지 검증.

    렌더링 없이 세션 로직만 확인하므로 base.html 의존성과 무관하게 동작한다.
    """

    def test_hand_is_dealt_when_session_empty(self):
        session = {}
        hand = _get_or_deal_hand(session)
        self.assertEqual(len(hand), HAND_SIZE)
        self.assertEqual(session[SESSION_HAND_KEY], hand)

    def test_hand_is_reused_on_repeat(self):
        session = {}
        first = _get_or_deal_hand(session)
        # 여러 번 다시 호출해도(=새로고침) 같은 손패가 유지되어야 한다.
        for _ in range(20):
            self.assertEqual(_get_or_deal_hand(session), first)

    def test_fresh_hand_after_session_cleared(self):
        session = {}
        _get_or_deal_hand(session)
        session.pop(SESSION_HAND_KEY)  # 신청 완료 시 세션 비움 시뮬레이션
        new_hand = _get_or_deal_hand(session)
        self.assertEqual(len(new_hand), HAND_SIZE)
        self.assertIn(SESSION_HAND_KEY, session)

    def test_corrupted_session_value_is_replaced(self):
        for bad in ["not-a-list", [], [1, 2, 3], None]:
            session = {SESSION_HAND_KEY: bad}
            hand = _get_or_deal_hand(session)
            self.assertEqual(len(hand), HAND_SIZE)


class AttackFlowTests(TestCase):
    def setUp(self):
        self.attacker = User.objects.create_user(username="alice", password="pw")
        self.defender = User.objects.create_user(username="bob", password="pw")
        self.client.force_login(self.attacker)

    def _get_hand(self):
        """공격 페이지를 열어 이번에 제공된 손패를 얻는다."""
        res = self.client.get(reverse("game:attack"))
        self.assertEqual(res.status_code, 200)
        hand = self.client.session[SESSION_HAND_KEY]
        self.assertEqual(len(hand), 5)
        return hand

    def test_attack_page_deals_five_cards_and_lists_opponents(self):
        res = self.client.get(reverse("game:attack"))
        self.assertContains(res, "bob")
        self.assertEqual(len(res.context["hand"]), 5)
        self.assertIn(self.defender, list(res.context["opponents"]))
        self.assertNotIn(self.attacker, list(res.context["opponents"]))

    def test_create_attack_from_dealt_card(self):
        hand = self._get_hand()
        res = self.client.post(
            reverse("game:attack"),
            {"opponent": self.defender.pk, "card": hand[0]},
        )
        self.assertRedirects(res, reverse("game:attack"))
        game = Game.objects.get()
        self.assertEqual(game.attacker, self.attacker)
        self.assertEqual(game.defender, self.defender)
        self.assertEqual(game.attacker_card, hand[0])
        self.assertEqual(game.status, Game.Status.WAITING)

    def test_card_not_in_hand_is_rejected(self):
        hand = self._get_hand()
        bogus = next(n for n in range(1, 11) if n not in hand)
        self.client.post(
            reverse("game:attack"),
            {"opponent": self.defender.pk, "card": bogus},
        )
        self.assertEqual(Game.objects.count(), 0)

    def test_cannot_attack_self(self):
        hand = self._get_hand()
        self.client.post(
            reverse("game:attack"),
            {"opponent": self.attacker.pk, "card": hand[0]},
        )
        self.assertEqual(Game.objects.count(), 0)

    def test_cancel_pending_attack(self):
        game = Game.objects.create(
            attacker=self.attacker, defender=self.defender, attacker_card=5
        )
        res = self.client.post(reverse("game:cancel_attack", args=[game.pk]))
        self.assertRedirects(res, reverse("game:attack"))
        self.assertEqual(Game.objects.count(), 0)

    def test_cannot_cancel_finished_game(self):
        game = Game.objects.create(
            attacker=self.attacker, defender=self.defender, attacker_card=5
        )
        game.resolve(defender_card=3)  # 종료 상태로 전환
        self.client.post(reverse("game:cancel_attack", args=[game.pk]))
        self.assertEqual(Game.objects.count(), 1)

    def test_cannot_cancel_others_attack(self):
        game = Game.objects.create(
            attacker=self.defender, defender=self.attacker, attacker_card=5
        )
        res = self.client.post(reverse("game:cancel_attack", args=[game.pk]))
        self.assertEqual(res.status_code, 404)
        self.assertEqual(Game.objects.count(), 1)
