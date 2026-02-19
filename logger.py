# logger.py

import csv
import os
import time


class GameLogger:

    def __init__(self):

        os.makedirs("data", exist_ok=True)

        timestamp = int(time.time())

        self.turn_file = f"data/turn_log_{timestamp}.csv"
        self.game_file = f"data/game_log_{timestamp}.csv"

        self.turn_count = 0
        self.game_id = timestamp

        self.init_files()


    def init_files(self):

        with open(self.turn_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "game_id",
                "turn",
                "player",
                "action",
                "card",
                "hand_size",
                "deck_size"
            ])

        with open(self.game_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "game_id",
                "winner",
                "total_turns"
            ])


    def log_turn(self, env, player, action):

        self.turn_count += 1

        state = env.get_state()

        if action == "DRAW":
            card = "DRAW"
        else:
            card = f"{action[0]}-{action[1]}"

        hand_size = len(state["hands"][player])
        deck_size = state["deck_size"]

        with open(self.turn_file, "a", newline="") as f:
            writer = csv.writer(f)

            writer.writerow([
                self.game_id,
                self.turn_count,
                player,
                action,
                card,
                hand_size,
                deck_size
            ])


    def log_game(self, env):

        winner = env.get_winner()

        with open(self.game_file, "a", newline="") as f:
            writer = csv.writer(f)

            writer.writerow([
                self.game_id,
                winner,
                self.turn_count
            ])
