"""
MCTS (蒙特卡洛树搜索) 智能体实现。
"""

import math
import random

from dlgo.gotypes import Player, Point
from dlgo.goboard import GameState, Move

__all__ = ["MCTSAgent"]


class MCTSNode:
    def __init__(self, game_state, parent=None, prior=1.0):
        self.game_state = game_state
        self.parent = parent
        self.children = []
        self.visit_count = 0
        self.value_sum = 0
        self.prior = prior

    @property
    def value(self):
        if self.visit_count == 0:
            return 0
        return self.value_sum / self.visit_count

    def is_leaf(self):
        return len(self.children) == 0

    def is_terminal(self):
        return self.game_state.is_over()

    def best_child(self, c=1.414):
        best_score = -float("inf")
        best_node = None

        for child in self.children:
            if child.visit_count == 0:
                return child

            uct = child.value + c * math.sqrt(
                math.log(self.visit_count) / child.visit_count
            )

            if uct > best_score:
                best_score = uct
                best_node = child

        return best_node

    def expand(self):
        moves = self.game_state.legal_moves()

        # 优化：去掉 resign
        moves = [m for m in moves if not m.is_resign]

        for move in moves:
            next_state = self.game_state.apply_move(move)
            child = MCTSNode(next_state, parent=self)
            child.move = move
            self.children.append(child)

        return random.choice(self.children) if self.children else self

    def backup(self, value):
        node = self
        while node is not None:
            node.visit_count += 1
            node.value_sum += value
            value = 1 - value  # 对手视角
            node = node.parent


class MCTSAgent:
    def __init__(self, num_rounds=500, temperature=1.0):
        self.num_rounds = num_rounds
        self.temperature = temperature

    def select_move(self, game_state: GameState) -> Move:
        root = MCTSNode(game_state)

        for _ in range(self.num_rounds):
            node = root

            # 1 Selection
            while not node.is_leaf() and not node.is_terminal():
                node = node.best_child()

            # 2 Expansion
            if not node.is_terminal():
                node = node.expand()

            # 3 Simulation
            value = self._simulate(node.game_state)

            # 4 Backup
            node.backup(value)

        return self._select_best_move(root)

    def _simulate(self, game_state):
        """
        优化版 rollout：
        - 限制深度（优化1）
        - 启发式走子（优化2）
        """
        current_state = game_state
        player = game_state.next_player

        max_depth = 20  # 🔥优化1：限制深度

        for _ in range(max_depth):
            if current_state.is_over():
                break

            moves = current_state.legal_moves()

            # 🔥优化2：去掉 resign
            moves = [m for m in moves if not m.is_resign]

            # 🔥优化2：优先落子（不选pass）
            play_moves = [m for m in moves if m.is_play]

            if play_moves:
                move = random.choice(play_moves)
            else:
                move = Move.pass_turn()

            current_state = current_state.apply_move(move)

        # 若未终局，用棋子数简单估计（启发式评估）
        if not current_state.is_over():
            black = 0
            white = 0

            for r in range(1, current_state.board.num_rows + 1):
                for c in range(1, current_state.board.num_cols + 1):
                    stone = current_state.board.get(Point(r, c))
                    if stone == Player.black:
                        black += 1
                    elif stone == Player.white:
                        white += 1

            if player == Player.black:
                return 1 if black > white else 0
            else:
                return 1 if white > black else 0

        # 已终局 → 用 scoring
        winner = current_state.winner()

        if winner == player:
            return 1
        else:
            return 0

    def _select_best_move(self, root):
        if not root.children:
            return Move.pass_turn()

        best_child = max(root.children, key=lambda c: c.visit_count)
        return best_child.move