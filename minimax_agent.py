from dlgo.gotypes import Player
from dlgo.goboard import Move, Point


class MinimaxAgent:

    def __init__(self, max_depth=2, evaluator=None):
        self.max_depth = max_depth
        self.evaluator = evaluator or self._default_evaluator

    # 对外接口
    def select_move(self, game_state):
        best_score = float("-inf")
        best_move = None

        moves = game_state.legal_moves()

        for move in moves:
            next_state = game_state.apply_move(move)
            score = self.alphabeta(
                next_state,
                self.max_depth - 1,
                float("-inf"),
                float("inf"),
                False
            )

            if score > best_score:
                best_score = score
                best_move = move

        # 防止 None 崩溃
        if best_move is None:
            return Move.pass_turn()

        return best_move

    
    # α-β剪枝
    def alphabeta(self, state, depth, alpha, beta, maximizing):

        if depth == 0 or state.is_over():
            return self._default_evaluator(state)

        moves = state.legal_moves()

        if maximizing:
            value = float("-inf")

            for move in moves:
                next_state = state.apply_move(move)
                value = max(value, self.alphabeta(
                    next_state, depth - 1, alpha, beta, False
                ))
                alpha = max(alpha, value)

                if alpha >= beta:
                    break

            return value

        else:
            value = float("inf")

            for move in moves:
                next_state = state.apply_move(move)
                value = min(value, self.alphabeta(
                    next_state, depth - 1, alpha, beta, True
                ))
                beta = min(beta, value)

                if beta <= alpha:
                    break

            return value

    # 修复评估函数
    def _default_evaluator(self, state):
        """
        安全版评估函数（不再访问 GoString.player）
        """

        board = state.board

        black = 0
        white = 0

        # 遍历合法点
        for r in range(1, board.num_rows + 1):
            for c in range(1, board.num_cols + 1):
                stone = board.get(Point(r, c))
                if stone is None:
                    continue
                if stone == Player.black:
                    black += 1
                elif stone == Player.white:
                    white += 1

        # 行动力
        mobility = len(state.legal_moves())

        if state.next_player == Player.black:
            return (black - white) + 0.1 * mobility
        else:
            return (white - black) + 0.1 * mobility

    # move排序
    def _get_ordered_moves(self, state):
        moves = state.legal_moves()

        def score(m):
            if m.is_play:
                return 2
            if m.is_pass:
                return 0
            return -1

        return sorted(moves, key=score, reverse=True)