from enum import Enum
import random
from typing import List, Dict, Tuple, Optional

# ========== 1. CARD DEFINITIONS ==========
class Color(Enum):
    RED = "R"
    BLUE = "B"
    GREEN = "G"
    YELLOW = "Y"
    WILD = "W"

class CardType(Enum):
    NUMBER = "NUMBER"
    SKIP = "SKIP"
    REVERSE = "REVERSE"
    DRAW_TWO = "DRAW_TWO"
    WILD = "WILD"
    WILD_DRAW_FOUR = "WILD_DRAW_FOUR"

class Card:
    """Represents a single UNO card"""
    def __init__(self, color: Color, value: str, card_type: CardType = CardType.NUMBER):
        self.color = color
        self.value = value
        self.type = card_type
        
    def __str__(self):
        if self.type == CardType.NUMBER:
            return f"{self.color.value}{self.value}"
        elif self.type == CardType.SKIP:
            return f"{self.color.value}SK"
        elif self.type == CardType.REVERSE:
            return f"{self.color.value}RV"
        elif self.type == CardType.DRAW_TWO:
            return f"{self.color.value}+2"
        elif self.type == CardType.WILD:
            return f"WILD"
        elif self.type == CardType.WILD_DRAW_FOUR:
            return f"WILD+4"
        return f"{self.color.value}{self.value[:2]}"
    
    def __repr__(self):
        return str(self)
    
    def matches(self, other_card: 'Card') -> bool:
        """Check if this card can be played on another card"""
        if self.color == Color.WILD or other_card.color == Color.WILD:
            return True
        return self.color == other_card.color or self.value == other_card.value

# ========== 2. DECK BUILDER WITH SPECIAL CARDS ==========
def create_deck() -> List[Card]:
    """Create a full UNO deck with ALL special cards"""
    deck = []
    colors = [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]
    
    # Number cards: 1-9 of each color (two of each except 0)
    for color in colors:
        # One zero card
        deck.append(Card(color, "0"))
        
        # Two of each 1-9
        for num in range(1, 10):
            deck.append(Card(color, str(num)))
            deck.append(Card(color, str(num)))
    
    # ===== SPECIAL ACTION CARDS (2 of each per color) =====
    for color in colors:
        # Skip cards
        for _ in range(2):
            deck.append(Card(color, "SK", CardType.SKIP))
        
        # Reverse cards  
        for _ in range(2):
            deck.append(Card(color, "RV", CardType.REVERSE))
        
        # Draw Two cards
        for _ in range(2):
            deck.append(Card(color, "+2", CardType.DRAW_TWO))
    
    # ===== WILD CARDS (4 of each) =====
    for _ in range(4):
        deck.append(Card(Color.WILD, "W", CardType.WILD))
    
    for _ in range(4):
        deck.append(Card(Color.WILD, "+4", CardType.WILD_DRAW_FOUR))
    
    return deck

def shuffle_deck(deck: List[Card]) -> List[Card]:
    """Shuffle the deck"""
    random.shuffle(deck)
    return deck

# ========== 3. GAME STATE CLASS ==========
class UnoGameState:
    """Tracks the complete state of a UNO game with special cards"""
    
    def __init__(self, num_players: int = 4):
        if not 2 <= num_players <= 4:
            raise ValueError("Number of players must be between 2 and 4")
        
        self.num_players = num_players
        self.current_player = 0
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.game_over = False
        self.winner = None
        
        # Special card state tracking
        self.draw_pile_count = 0  # Cards to draw (for +2 and +4 chains)
        self.skip_next = False    # Skip next player
        self.pending_color = None # For wild card color choice
        
        # NEW: Track drawn card for "play after draw" rule
        self.last_drawn_card = None
        self.can_play_drawn_card = False
        
        # Card piles
        self.deck = []
        self.discard_pile = []
        self.player_hands = []
        
        # Game stats
        self.turn_count = 0
        self.players_uno = [False] * num_players
    
    def initialize_game(self):
        """Set up a new game with special cards"""
        # Create and shuffle deck WITH special cards
        self.deck = shuffle_deck(create_deck())
        
        # Initialize empty hands
        self.player_hands = [[] for _ in range(self.num_players)]
        
        # Deal 7 cards to each player
        for _ in range(7):
            for player_idx in range(self.num_players):
                if self.deck:
                    self.player_hands[player_idx].append(self.deck.pop())
        
        # Start discard pile with one card
        if self.deck:
            top_card = self.deck.pop()
            # Ensure first card is not a wild or special
            while (top_card.color == Color.WILD or 
                   top_card.type in [CardType.SKIP, CardType.REVERSE, CardType.DRAW_TWO]) and len(self.deck) > 1:
                self.deck.insert(0, top_card)
                top_card = self.deck.pop()
            self.discard_pile.append(top_card)
        
        # Reset special card states
        self.draw_pile_count = 0
        self.skip_next = False
        self.pending_color = None
        self.last_drawn_card = None
        self.can_play_drawn_card = False
        
        print(f"Game initialized with {len(self.deck)} cards in deck (includes special cards)")
    
    def get_top_card(self) -> Card:
        """Get current top card on discard pile"""
        if not self.discard_pile:
            return None
        
        top_card = self.discard_pile[-1]
        
        # If top card is wild and we have a pending color,
        # return a virtual card with the chosen color
        if top_card.color == Color.WILD and self.pending_color and self.pending_color != Color.WILD:
            return Card(self.pending_color, top_card.value, top_card.type)
        
        return top_card
    
    def get_player_hand(self, player_idx: int) -> List[Card]:
        """Get copy of player's hand"""
        return self.player_hands[player_idx].copy()
    
    def draw_card(self, player_idx: int) -> Optional[Card]:
        """Player draws a card from deck"""
        if not self.deck:
            self._reshuffle_deck()
        
        if self.deck:
            card = self.deck.pop()
            self.player_hands[player_idx].append(card)
            return card
        return None
    
    def _reshuffle_deck(self):
        """Reshuffle discard pile (except top card) into deck"""
        if len(self.discard_pile) > 1:
            top_card = self.discard_pile.pop()
            self.deck = self.discard_pile
            self.discard_pile = [top_card]
            shuffle_deck(self.deck)
    
    # ========== 4. ENHANCED GAME LOGIC WITH "PLAY AFTER DRAW" ==========
    def get_legal_actions(self, player_idx: int) -> List[Tuple[str, Optional[Card]]]:
        """
        Get all legal actions for current player.
        Returns list of (action_type, card) tuples.
        """
        legal_actions = []
        top_card = self.get_top_card()
        
        # If there's a draw pile, special rules apply
        if self.draw_pile_count > 0:
            # Can only play matching draw cards or draw the pile
            for card in self.player_hands[player_idx]:
                if top_card and self._can_play_card(card, top_card, is_draw_pile=True):
                    legal_actions.append(('play', card))
            
            # Can always draw the accumulated cards
            legal_actions.append(('draw', None))
            return legal_actions
        
        # Normal play checking
        for card in self.player_hands[player_idx]:
            if self._can_play_card(card, top_card):
                legal_actions.append(('play', card))
        
        # NEW: If player just drew and can play that card
        if self.can_play_drawn_card and self.last_drawn_card and player_idx == self.current_player:
            # The drawn card is already in the hand, but we note it's special
            pass
        
        # Always allow drawing a card
        legal_actions.append(('draw', None))
        
        return legal_actions
    
    def _can_play_card(self, card: Card, top_card: Card, is_draw_pile: bool = False) -> bool:
        """Check if a card can be played on the current top card"""
        if not top_card:
            return True
        
        # Wild cards can always be played (simplified - no Wild Draw Four challenge rule)
        if card.color == Color.WILD:
            return True
        
        # If there's a pending color from a wild card
        if self.pending_color and self.pending_color != Color.WILD:
            return card.color == self.pending_color
        
        # Special draw pile rules
        if is_draw_pile:
            # In a draw pile, you can only play matching draw cards
            if top_card.type == CardType.DRAW_TWO:
                return card.type == CardType.DRAW_TWO and (card.color == top_card.color or card.color == Color.WILD)
            elif top_card.type == CardType.WILD_DRAW_FOUR:
                return card.type == CardType.WILD_DRAW_FOUR
            return False
        
        # Normal matching rules
        return card.matches(top_card)
    
    # ========== NEW: DRAW WITH OPTION TO PLAY ==========
    def draw_with_option(self, player_idx: int) -> Tuple[Optional[Card], bool]:
        """
        Draw a card and check if it's playable.
        Returns: (drawn_card, is_playable)
        
        Member 2 should use this method instead of apply_action('draw')
        """
        if player_idx != self.current_player:
            print(f"Not player {player_idx}'s turn!")
            return None, False
        
        if self.draw_pile_count > 0:
            # Draw pile situation - must draw all, can't play
            print(f"Player {player_idx} draws {self.draw_pile_count} cards!")
            for _ in range(self.draw_pile_count):
                self.draw_card(player_idx)
            self.draw_pile_count = 0
            
            # After drawing from draw pile, turn ends
            self._advance_turn()
            return None, False
        else:
            # Normal draw
            drawn_card = self.draw_card(player_idx)
            print(f"Player {player_idx} drew: {drawn_card}")
            
            # Check if drawn card is playable
            top_card = self.get_top_card()
            is_playable = drawn_card and self._can_play_card(drawn_card, top_card)
            
            if is_playable:
                print(f"  ⚡ Drawn card {drawn_card} is PLAYABLE!")
                print(f"  Player may choose to play it or end turn.")
                
                # Store for potential play
                self.last_drawn_card = drawn_card
                self.can_play_drawn_card = True
            else:
                print(f"  Drawn card {drawn_card} is not playable. Turn ends.")
                self._advance_turn()
                self.last_drawn_card = None
                self.can_play_drawn_card = False
            
            return drawn_card, is_playable
    
    def play_drawn_card(self, player_idx: int, chosen_color: Optional[Color] = None) -> bool:
        """
        Play the card that was just drawn.
        Must be called immediately after draw_with_option() if card is playable.
        """
        if player_idx != self.current_player:
            print(f"Not player {player_idx}'s turn!")
            return False
        
        if not self.can_play_drawn_card or not self.last_drawn_card:
            print(f"No playable drawn card available!")
            return False
        
        card = self.last_drawn_card
        
        # For wild cards, check color was chosen
        if card.type in [CardType.WILD, CardType.WILD_DRAW_FOUR]:
            if chosen_color is None or chosen_color == Color.WILD:
                print(f"Must choose a valid color (RED/BLUE/GREEN/YELLOW) for wild card!")
                return False
            self.pending_color = chosen_color
        
        # Remove card from hand (it was just added by draw_card)
        self.player_hands[player_idx].remove(card)
        self.discard_pile.append(card)
        
        # Apply special card effects
        self._apply_special_effect(card, player_idx)
        
        # Check for UNO
        if len(self.player_hands[player_idx]) == 1:
            self.players_uno[player_idx] = True
            print(f"Player {player_idx} says UNO!")
        
        # Check for win
        if len(self.player_hands[player_idx]) == 0:
            self.game_over = True
            self.winner = player_idx
            print(f"🎉 Player {player_idx} wins!")
            self.last_drawn_card = None
            self.can_play_drawn_card = False
            return True
        
        # Move to next player (handling skip)
        self._advance_turn_with_skip()
        
        # Reset drawn card state
        self.last_drawn_card = None
        self.can_play_drawn_card = False
        
        return True
    
    def end_turn_after_draw(self, player_idx: int) -> bool:
        """
        End turn after drawing (player chooses not to play drawn card).
        """
        if player_idx != self.current_player:
            print(f"Not player {player_idx}'s turn!")
            return False
        
        # Player chose not to play the drawn card
        print(f"Player {player_idx} chooses not to play the drawn card.")
        
        # Reset drawn card state
        self.last_drawn_card = None
        self.can_play_drawn_card = False
        
        # Advance turn
        self._advance_turn()
        return True
    
    def apply_action(self, player_idx: int, action: str, card: Optional[Card] = None, 
                     chosen_color: Optional[Color] = None) -> bool:
        """
        Apply a player's action (for backward compatibility).
        NOTE: For drawing, use draw_with_option() instead for full "play after draw" rule!
        """
        if self.game_over:
            return False
        
        if player_idx != self.current_player:
            print(f"Not player {player_idx}'s turn!")
            return False
        
        if action == 'draw':
            # Use the new method but auto-end turn (simplified backward compatibility)
            drawn_card, is_playable = self.draw_with_option(player_idx)
            if is_playable:
                # Auto-end turn for backward compatibility
                self.end_turn_after_draw(player_idx)
            return True
                
        elif action == 'play' and card:
            # Check if this is a regular play (not a drawn card play)
            legal_actions = self.get_legal_actions(player_idx)
            
            if not any(act[0] == 'play' and str(act[1]) == str(card) for act in legal_actions):
                print(f"Invalid action by player {player_idx}: Cannot play {card}")
                return False
            
            # For wild cards, check color was chosen
            if card.type in [CardType.WILD, CardType.WILD_DRAW_FOUR]:
                if chosen_color is None or chosen_color == Color.WILD:
                    print(f"Must choose a valid color (RED/BLUE/GREEN/YELLOW) for wild card!")
                    return False
                self.pending_color = chosen_color
            
            # Remove card from hand
            self.player_hands[player_idx].remove(card)
            self.discard_pile.append(card)
            
            # Apply special card effects
            self._apply_special_effect(card, player_idx)
            
            # Check for UNO
            if len(self.player_hands[player_idx]) == 1:
                self.players_uno[player_idx] = True
                print(f"Player {player_idx} says UNO!")
            
            # Check for win
            if len(self.player_hands[player_idx]) == 0:
                self.game_over = True
                self.winner = player_idx
                print(f"🎉 Player {player_idx} wins!")
                return True
            
            # Move to next player (handling skip)
            self._advance_turn_with_skip()
            
            return True
        
        print(f"Invalid action by player {player_idx}")
        return False
    
    def _apply_special_effect(self, card: Card, player_idx: int):
        """Apply the effect of a special card"""
        if card.type == CardType.SKIP:
            self.skip_next = True
            print(f"⏭️  SKIP! Next player will be skipped.")
            
        elif card.type == CardType.REVERSE:
            self.direction *= -1
            direction_text = "counter-clockwise" if self.direction == -1 else "clockwise"
            print(f"🔄 REVERSE! Direction now {direction_text}")
            
            # Special rule for 2 players: Reverse acts as Skip
            if self.num_players == 2:
                self.skip_next = True
                print(f"  (2-player game: Reverse acts as Skip)")
            
        elif card.type == CardType.DRAW_TWO:
            self.draw_pile_count += 2
            print(f"➕2 DRAW TWO! Next player draws {self.draw_pile_count} cards")
            
        elif card.type == CardType.WILD_DRAW_FOUR:
            self.draw_pile_count += 4
            print(f"🎨➕4 WILD DRAW FOUR! Next player draws {self.draw_pile_count} cards")
            
        elif card.type == CardType.WILD:
            print(f"🎨 WILD! Color changes to {self.pending_color}")
    
    def _advance_turn_with_skip(self):
        """Move to next player's turn with skip handling"""
        if self.skip_next:
            # Skip happens by advancing twice
            self.current_player = (self.current_player + self.direction) % self.num_players
            self.skip_next = False
            print(f"⏭️  Player {self.current_player} was skipped!")
            # Advance again to the actual next player
            self.current_player = (self.current_player + self.direction) % self.num_players
        else:
            self.current_player = (self.current_player + self.direction) % self.num_players
        
        self.turn_count += 1
        
        # Reset pending color if current card isn't wild
        if self.pending_color:
            top_card = self.get_top_card()
            if top_card and top_card.color != Color.WILD:
                self.pending_color = None
    
    def _advance_turn(self):
        """Simple turn advancement"""
        self.turn_count += 1
        self.current_player = (self.current_player + self.direction) % self.num_players
    
    def is_terminal(self) -> bool:
        """Check if game is over"""
        return self.game_over
    
    # ========== 5. UTILITY METHODS ==========
    def get_game_state_summary(self) -> Dict:
        """Return a summary of game state for display/logging."""
        return {
            'current_player': self.current_player,
            'top_card': str(self.get_top_card()) if self.get_top_card() else None,
            'direction': 'clockwise' if self.direction == 1 else 'counter-clockwise',
            'hand_sizes': [len(hand) for hand in self.player_hands],
            'game_over': self.game_over,
            'winner': self.winner,
            'turn_count': self.turn_count,
            'deck_remaining': len(self.deck),
            'draw_pile_count': self.draw_pile_count,
            'skip_next': self.skip_next,
            'pending_color': str(self.pending_color) if self.pending_color else None,
            'can_play_drawn_card': self.can_play_drawn_card,
            'last_drawn_card': str(self.last_drawn_card) if self.last_drawn_card else None
        }
    
    def get_public_info(self, player_idx: int) -> Dict:
        """
        Get information visible to a specific player.
        Used by bots to make decisions.
        """
        return {
            'my_hand': self.get_player_hand(player_idx),
            'my_hand_size': len(self.get_player_hand(player_idx)),
            'top_card': self.get_top_card(),
            'current_player': self.current_player,
            'num_players': self.num_players,
            'hand_sizes': [len(hand) for hand in self.player_hands],
            'direction': self.direction,
            'legal_actions': self.get_legal_actions(player_idx),
            'draw_pile_count': self.draw_pile_count,
            'skip_next': self.skip_next,
            'pending_color': self.pending_color,
            'can_play_drawn_card': self.can_play_drawn_card if player_idx == self.current_player else False,
            'last_drawn_card': self.last_drawn_card if player_idx == self.current_player else None
        }