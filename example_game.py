"""
EXAMPLE UNO GAME USING THE ENGINE (FIXED VERSION)
Shows how to use the UnoGameState for a complete game with "play after draw" rule
"""

from UNO_strategic_game.uno_env import UnoGameState, Color, Card, CardType
import time

def print_game_state(game, player_idx):
    """Print current game state for a player"""
    print("\n" + "="*60)
    print(f"PLAYER {player_idx}'s VIEW")
    print("="*60)
    
    # Top card
    top_card = game.get_top_card()
    print(f"\n📌 TOP CARD: {top_card}")
    
    # Game state info
    if game.pending_color:
        print(f"   Current color: {game.pending_color.name}")
    
    if game.draw_pile_count > 0:
        print(f"⚠️  Draw pile: {game.draw_pile_count} cards!")
    
    if game.skip_next:
        print(f"⚠️  Next player will be SKIPPED!")
    
    # Direction
    direction = "clockwise" if game.direction == 1 else "counter-clockwise"
    print(f"   Direction: {direction}")
    print(f"   Current player: {game.current_player}")
    
    # Player's hand
    hand = game.get_player_hand(player_idx)
    print(f"\n🎴 YOUR HAND ({len(hand)} cards):")
    for i, card in enumerate(hand, 1):
        print(f"  {i:2d}. {card}")
    
    # Other players
    print(f"\n👥 OTHER PLAYERS:")
    for i in range(game.num_players):
        if i != player_idx:
            hand_size = len(game.player_hands[i])
            uno_status = " 🚨 UNO!" if game.players_uno[i] else ""
            print(f"  Player {i}: {hand_size} cards{uno_status}")

def human_turn(game, player_idx):
    """Handle human player's turn with proper "play after draw" rule"""
    print(f"\n✅ PLAYER {player_idx}'S TURN")
    
    # Get legal actions
    legal_actions = game.get_legal_actions(player_idx)
    
    if not legal_actions:
        print("No legal actions available!")
        return False
    
    # Display options
    print("\nAvailable actions:")
    options = []
    
    # Playable cards
    playable_cards = []
    for action_type, card in legal_actions:
        if action_type == 'play':
            playable_cards.append(card)
            print(f"  [P{len(playable_cards)}] Play {card}")
    
    # Draw option
    print(f"  [D] Draw a card")
    
    # Get choice
    while True:
        choice = input("\nEnter your choice (e.g., 'P1' to play first card, 'D' to draw): ").strip().upper()
        
        if choice == 'D':
            # NEW: Use draw_with_option() API for "play after draw" rule
            print(f"Player {player_idx} chooses to draw")
            drawn_card, is_playable = game.draw_with_option(player_idx)
            
            if is_playable:
                print(f"\n🎯 You drew {drawn_card} which is PLAYABLE!")
                print("Do you want to play it?")
                
                while True:
                    play_choice = input("Play drawn card? (Y/N): ").strip().upper()
                    if play_choice in ['Y', 'N']:
                        break
                    print("Please enter Y or N")
                
                if play_choice == 'Y':
                    # Play the drawn card
                    chosen_color = None
                    if drawn_card and drawn_card.color == Color.WILD:
                        print("\n🎨 Choose a color for your wild card:")
                        print("  1. RED")
                        print("  2. BLUE")
                        print("  3. GREEN")
                        print("  4. YELLOW")
                        
                        while True:
                            color_choice = input("Enter choice (1-4): ").strip()
                            if color_choice in ['1', '2', '3', '4']:
                                color_map = {
                                    '1': Color.RED,
                                    '2': Color.BLUE,
                                    '3': Color.GREEN,
                                    '4': Color.YELLOW
                                }
                                chosen_color = color_map[color_choice]
                                break
                            print("Please enter 1, 2, 3, or 4")
                    
                    success = game.play_drawn_card(player_idx, chosen_color)
                    if success:
                        print(f"✅ Played drawn card {drawn_card}!")
                    else:
                        print(f"❌ Failed to play {drawn_card}")
                else:
                    # Choose not to play
                    game.end_turn_after_draw(player_idx)
                    print(f"⏭️ Chose not to play {drawn_card}. Turn ends.")
            else:
                # Drawn card not playable, turn already ended
                print(f"📥 Drew {drawn_card}. Turn ends.")
            
            return True
            
        elif choice.startswith('P') and choice[1:].isdigit():
            card_index = int(choice[1:]) - 1
            if 0 <= card_index < len(playable_cards):
                card = playable_cards[card_index]
                
                # For wild cards, ask for color
                chosen_color = None
                if card and card.color == Color.WILD:
                    print("\n🎨 Choose a color for your wild card:")
                    print("  1. RED")
                    print("  2. BLUE")
                    print("  3. GREEN")
                    print("  4. YELLOW")
                    
                    while True:
                        color_choice = input("Enter choice (1-4): ").strip()
                        if color_choice in ['1', '2', '3', '4']:
                            color_map = {
                                '1': Color.RED,
                                '2': Color.BLUE,
                                '3': Color.GREEN,
                                '4': Color.YELLOW
                            }
                            chosen_color = color_map[color_choice]
                            break
                        print("Please enter 1, 2, 3, or 4")
                
                # Play the card
                print(f"Player {player_idx} chooses to play {card}")
                success = game.apply_action(player_idx, 'play', card, chosen_color)
                
                if success:
                    return True
                else:
                    print("❌ Invalid move! Try again.")
                    continue
            else:
                print(f"Please enter P1-P{len(playable_cards)} or D")
        else:
            print(f"Please enter P1-P{len(playable_cards)} or D")

def simple_bot_turn(game, player_idx):
    """Simple bot player with proper "play after draw" rule"""
    print(f"\n🤖 BOT PLAYER {player_idx}'S TURN")
    time.sleep(1)  # Pause to make it feel more natural
    
    legal_actions = game.get_legal_actions(player_idx)
    
    # Try to play first playable card
    for action_type, card in legal_actions:
        if action_type == 'play':
            # For wild cards, choose a color
            chosen_color = None
            if card and card.color == Color.WILD:
                # Simple strategy: choose color with most cards in hand
                color_counts = {}
                for c in game.player_hands[player_idx]:
                    if c.color != Color.WILD:
                        color_counts[c.color] = color_counts.get(c.color, 0) + 1
                
                if color_counts:
                    # Choose most common color
                    chosen_color = max(color_counts.items(), key=lambda x: x[1])[0]
                else:
                    # Fallback to RED
                    chosen_color = Color.RED
            
            print(f"Bot {player_idx} plays {card}")
            if chosen_color:
                print(f"  (chooses color: {chosen_color.name})")
            
            game.apply_action(player_idx, 'play', card, chosen_color)
            return True
    
    # If no playable cards, draw with option to play
    print(f"Bot {player_idx} draws a card")
    drawn_card, is_playable = game.draw_with_option(player_idx)
    
    if is_playable:
        # Bot always plays if possible (simple strategy)
        print(f"Bot drew {drawn_card} which is playable!")
        
        chosen_color = None
        if drawn_card and drawn_card.color == Color.WILD:
            # Choose a color for wild card
            chosen_color = Color.RED  # Simple choice
        
        success = game.play_drawn_card(player_idx, chosen_color)
        if success:
            print(f"Bot plays the drawn card!")
        else:
            print(f"Bot couldn't play the drawn card")
    else:
        # Card not playable, turn already ended
        print(f"Bot drew {drawn_card}. Turn ends.")
    
    return True

def run_example_game(num_players=3, human_player_idx=0):
    """Run a complete example game"""
    print("="*60)
    print("🏁 STARTING UNO EXAMPLE GAME (WITH PLAY-AFTER-DRAW RULE)")
    print("="*60)
    
    # Create game
    game = UnoGameState(num_players=num_players)
    game.initialize_game()
    
    print(f"Game created with {num_players} players")
    print(f"You are Player {human_player_idx}")
    print(f"Each player starts with 7 cards")
    print(f"Deck has {len(game.deck)} cards remaining")
    
    # Game loop
    turn_count = 0
    while not game.game_over:
        turn_count += 1
        print(f"\n{'='*60}")
        print(f"TURN {turn_count}")
        print(f"{'='*60}")
        
        current_player = game.current_player
        
        # Show game state for human
        if current_player == human_player_idx:
            print_game_state(game, human_player_idx)
        
        # Take turn
        if current_player == human_player_idx:
            human_turn(game, current_player)
        else:
            # Bot player
            simple_bot_turn(game, current_player)
        
        # Check if game ended
        if game.game_over:
            print(f"\n{'🎉'*20}")
            print(f"GAME OVER! Player {game.winner} WINS!")
            print(f"{'🎉'*20}")
            
            # Show final state
            print("\nFinal game state:")
            summary = game.get_game_state_summary()
            for key, value in summary.items():
                print(f"  {key}: {value}")
            break
        
        # Show turn result
        print(f"\nTurn completed. Next player: {game.current_player}")
        time.sleep(1)  # Brief pause

def test_specific_scenario():
    """Test a specific scenario to demonstrate special cards"""
    print("\n" + "="*60)
    print("TESTING SPECIAL CARD SCENARIO")
    print("="*60)
    
    # Create a controlled scenario
    game = UnoGameState(num_players=3)
    
    # Manually set up cards
    game.player_hands = [
        [Card(Color.RED, "5"), Card(Color.WILD, "W", CardType.WILD)],  # Player 0
        [Card(Color.BLUE, "3"), Card(Color.RED, "SK", CardType.SKIP)],  # Player 1
        [Card(Color.GREEN, "+2", CardType.DRAW_TWO), Card(Color.YELLOW, "RV", CardType.REVERSE)]  # Player 2
    ]
    
    game.discard_pile = [Card(Color.RED, "2")]
    game.current_player = 0
    game.draw_pile_count = 0
    game.skip_next = False
    game.pending_color = None
    
    print("\n🎮 Scenario: Player 0's turn")
    print("Player 0 has: RED 5 and WILD")
    print("Top card: RED 2")
    print("\nPlayer 0 can play either card!")
    
    # Show state
    print_game_state(game, 0)
    
    # Simulate playing wild card
    print("\n🤔 Let's play the WILD card and choose BLUE...")
    time.sleep(2)
    
    success = game.apply_action(0, 'play', Card(Color.WILD, "W", CardType.WILD), chosen_color=Color.BLUE)
    print(f"Play successful: {success}")
    print(f"New top card: {game.get_top_card()}")
    print(f"Pending color: {game.pending_color}")
    
    # Now Player 1's turn
    print("\n🔄 Now it's Player 1's turn")
    print("Player 1 must play a BLUE card or another wild")
    print("Player 1 has: BLUE 3 and RED SKIP")
    print("Player 1 can play BLUE 3!")
    
    # Show state for player 1
    print_game_state(game, 1)
    
    print("\n✅ Scenario test complete!")

# ========== QUICK DEMO ==========
def quick_demo():
    """Quick demonstration of the engine"""
    print("Quick UNO Engine Demo")
    print("-" * 40)
    
    # Create a simple 2-player game
    game = UnoGameState(num_players=2)
    game.initialize_game()
    
    print(f"Created 2-player game")
    print(f"Player 0 hand: {[str(c) for c in game.get_player_hand(0)[:3]]}...")
    print(f"Player 1 hand: {[str(c) for c in game.get_player_hand(1)[:3]]}...")
    print(f"Top card: {game.get_top_card()}")
    print(f"Current player: {game.current_player}")
    
    # Show legal moves for player 0
    legal = game.get_legal_actions(0)
    print(f"\nPlayer 0 legal actions:")
    for action, card in legal:
        if action == 'play':
            print(f"  Play {card}")
        else:
            print(f"  Draw a card")
    
    # Play a card if possible
    for action, card in legal:
        if action == 'play':
            print(f"\nPlaying {card}...")
            success = game.apply_action(0, 'play', card)
            print(f"Success: {success}")
            print(f"New current player: {game.current_player}")
            break
    
    print("\n✅ Demo complete!")

if __name__ == "__main__":
    print("UNO ENGINE EXAMPLE GAMES")
    print("Choose an example to run:")
    print("  1. Quick demo (fast)")
    print("  2. Special card scenario")
    print("  3. Full 3-player game (WITH PLAY-AFTER-DRAW FIX)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        quick_demo()
    elif choice == "2":
        test_specific_scenario()
    elif choice == "3":
        run_example_game(num_players=3, human_player_idx=0)
    else:
        print("Running full game by default...")
        run_example_game(num_players=3, human_player_idx=0)