# bot_player.py
import random
from collections import defaultdict, Counter
from typing import Optional, Tuple, Dict, Any, List

# Import these from uno_env.py in your project
# from uno_env import Color, CardType, Card, UnoGameState

# If you prefer not to import directly, Member 4 can inject these.
# But best is: from uno_env import Color, CardType

class BaseBot:
    """
    All bots must implement:
      choose_action(public_info) -> (action, card, chosen_color)
    where:
      action: 'play' or 'draw'
      card: Card object or None
      chosen_color: Color or None (required if playing WILD or WILD_DRAW_FOUR)
    """
    def __init__(self, player_id: int, seed: Optional[int] = None):
        self.player_id = player_id
        self.rng = random.Random(seed)

    def observe(self, event: Dict[str, Any]) -> None:
        """
        Optional hook for learning/prediction.
        Member 4 / logger can call this once per turn.
        Recommended event format:
          {
            "type": "play"|"draw",
            "player": int,
            "card": Card|None,
            "chosen_color": Color|None,
            "top_card_after": Card,
            "turn": int,
          }
        """
        pass

    def choose_action(self, public_info: Dict[str, Any]):
        raise NotImplementedError


class RandomBot(BaseBot):
    def choose_action(self, public_info: Dict[str, Any]):
        legal = public_info["legal_actions"]  # List[Tuple[str, Optional[Card]]]
        action, card = self.rng.choice(legal)

        chosen_color = None
        if action == "play" and getattr(card, "color", None).name == "WILD":
            chosen_color = self._pick_best_color(public_info)

        return action, card, chosen_color

    def _pick_best_color(self, public_info: Dict[str, Any]):
        from uno_env import Color  # local import to avoid circular issues
        hand = public_info["my_hand"]
        counts = Counter([c.color for c in hand if c.color != Color.WILD])
        if not counts:
            return self.rng.choice([Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW])
        return counts.most_common(1)[0][0]


class RuleBasedBot(BaseBot):
    """
    Simple heuristics:
      - Prefer playing over drawing
      - Prefer action cards when opponent next has low hand size
      - Prefer playing color you have a lot of
      - For wild: choose your most common color
    """
    def choose_action(self, public_info: Dict[str, Any]):
        from uno_env import Color, CardType

        legal = public_info["legal_actions"]
        hand = public_info["my_hand"]
        hand_sizes = public_info["hand_sizes"]
        num_players = public_info["num_players"]
        direction = public_info["direction"]
        current_player = public_info["current_player"]

        # Identify next player (for simple targeting)
        next_player = (current_player + direction) % num_players
        next_size = hand_sizes[next_player]

        # If draw pile is active, legal is (play matching draw cards...) + ('draw', None)
        # We'll still score play actions higher.
        def score(action_card):
            action, card = action_card
            if action == "draw":
                return -999

            # Base prefer playing
            s = 100

            # Prefer shedding wilds late-ish? (optional) For now treat wild as good.
            if card.type in (CardType.WILD, CardType.WILD_DRAW_FOUR):
                s += 10

            # Prefer action cards if next opponent is close to winning
            if next_size <= 3 and card.type in (CardType.SKIP, CardType.REVERSE, CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR):
                s += 25

            # Prefer playing a color you have many of (keeps flexibility)
            if card.color != Color.WILD:
                color_count = sum(1 for c in hand if c.color == card.color)
                s += color_count * 2

            # Prefer DrawTwo / Wild+4 generally a bit
            if card.type == CardType.DRAW_TWO:
                s += 8
            if card.type == CardType.WILD_DRAW_FOUR:
                s += 12
            if card.type == CardType.SKIP:
                s += 6
            if card.type == CardType.REVERSE:
                s += 4

            return s

        best_action, best_card = max(legal, key=score)

        chosen_color = None
        if best_action == "play" and best_card.color.name == "WILD":
            chosen_color = self._pick_best_color(public_info)

        return best_action, best_card, chosen_color

    def _pick_best_color(self, public_info):
        from uno_env import Color
        hand = public_info["my_hand"]
        counts = Counter([c.color for c in hand if c.color != Color.WILD])
        if not counts:
            return self.rng.choice([Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW])
        return counts.most_common(1)[0][0]


class PredictiveBot(BaseBot):
    """
    Predictive bot tracks each opponent's played colors and prefers actions
    that avoid giving the next player their preferred color.

    Uses Laplace smoothing:
      P(color|opp) = (count + 1) / (total + 4)
    """
    def __init__(self, player_id: int, seed: Optional[int] = None):
        super().__init__(player_id, seed)
        self.color_play_counts = defaultdict(Counter)  # opp -> Counter(Color)
        self.total_color_plays = Counter()             # opp -> int

    def observe(self, event: Dict[str, Any]) -> None:
        # Only learn from plays (draws don't reveal color preference)
        if event.get("type") != "play":
            return
        p = event.get("player")
        if p is None or p == self.player_id:
            return

        card = event.get("card")
        chosen_color = event.get("chosen_color")  # for wilds

        # If a wild is played, treat chosen_color as the "intent"
        color = None
        if card is not None and getattr(card, "color", None) is not None:
            if card.color.name == "WILD" and chosen_color is not None:
                color = chosen_color
            else:
                color = card.color

        # ignore wild-as-color itself
        from uno_env import Color
        if color is not None and color != Color.WILD:
            self.color_play_counts[p][color] += 1
            self.total_color_plays[p] += 1

    def _p_opp_prefers(self, opp_id: int, color) -> float:
        from uno_env import Color
        # Laplace smoothing over 4 colors
        total = self.total_color_plays[opp_id]
        return (self.color_play_counts[opp_id][color] + 1) / (total + 4)

    def choose_action(self, public_info: Dict[str, Any]):
        from uno_env import Color, CardType

        legal = public_info["legal_actions"]
        hand = public_info["my_hand"]
        hand_sizes = public_info["hand_sizes"]
        num_players = public_info["num_players"]
        direction = public_info["direction"]
        current_player = public_info["current_player"]

        next_player = (current_player + direction) % num_players
        next_size = hand_sizes[next_player]

        # Precompute our color counts (for choosing wild color + flexibility)
        my_color_counts = Counter([c.color for c in hand if c.color != Color.WILD])

        def pick_wild_color_anti_next() -> Color:
            # Choose color that next player least prefers, but still reasonable for us
            if not my_color_counts:
                candidates = [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]
            else:
                # biased toward our most common colors
                candidates = [c for c, _ in my_color_counts.most_common()]
                # ensure all 4 are possible fallbacks
                for c in [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]:
                    if c not in candidates:
                        candidates.append(c)

            # score: we like colors we hold, but dislike giving next player their preferred color
            best_c = None
            best_s = -1e9
            for c in candidates:
                have = my_color_counts[c]
                opp_pref = self._p_opp_prefers(next_player, c)
                s = have * 3 - opp_pref * 10
                if s > best_s:
                    best_s = s
                    best_c = c
            return best_c

        def score(action_card: Tuple[str, Optional[Any]]):
            action, card = action_card
            if action == "draw":
                return -999

            s = 100

            # When opponent is close to winning, disrupt them
            if next_size <= 3 and card.type in (CardType.SKIP, CardType.REVERSE, CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR):
                s += 35

            # Prefer getting rid of action cards reasonably
            if card.type == CardType.DRAW_TWO:
                s += 10
            if card.type == CardType.SKIP:
                s += 8
            if card.type == CardType.REVERSE:
                s += 5
            if card.type == CardType.WILD_DRAW_FOUR:
                s += 14
            if card.type == CardType.WILD:
                s += 10

            # Prediction component:
            # If we play a non-wild card, it sets a color context. Avoid next player's favorite.
            if card.color != Color.WILD:
                opp_pref = self._p_opp_prefers(next_player, card.color)
                s -= opp_pref * 40  # strong penalty

                # flexibility: play colors we have more of
                s += my_color_counts[card.color] * 2

            # If wild, we can choose an anti-opponent color, so reward more
            else:
                s += 8

            return s

        best_action, best_card = max(legal, key=score)

        chosen_color = None
        if best_action == "play" and best_card.color == Color.WILD:
            chosen_color = pick_wild_color_anti_next()

        return best_action, best_card, chosen_color
