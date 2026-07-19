from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Game
from .views_start import SESSION_HAND_KEY

User = get_user_model()


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
