import random
from dlgo import GameState, Move

__all__ = ["RandomAgent"]


class RandomAgent:
    """随机落子智能体 - 第一小问实现"""

    def __init__(self):
        """初始化随机智能体（无需特殊参数）"""
      
    def select_move(self, game_state: GameState) -> Move:
        """选择随机合法棋步"""
         ## 获取所有合法棋步
        candidates = game_state.legal_moves()

        # 优先选择“正常落子”（避免一开始就 pass 或 resign）
        play_moves = [m for m in candidates if m.is_play]

        if play_moves:
            return random.choice(play_moves)

        # 如果没有可落子，再从所有合法动作中选
        if candidates:
            return random.choice(candidates)

        return Move.pass_turn()

        pass


# 便捷函数（向后兼容 play.py）
def random_agent(game_state: GameState) -> Move:
    """函数接口，兼容 play.py 的调用方式"""
    agent = RandomAgent()
    return agent.select_move(game_state)