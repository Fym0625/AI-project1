import argparse
import random
import time

from dlgo import GameState, Player, Point
from dlgo.goboard import Move

# Random Agent
def random_agent(game_state):
    try:
        from agents.random_agent import RandomAgent
        agent = RandomAgent()
        return agent.select_move(game_state)
    except ImportError:
        moves = game_state.legal_moves()
        return random.choice(moves)


# MCTS Agents
from agents.mcts_agent import MCTSAgent

_mcts_100 = MCTSAgent(num_rounds=100)
_mcts_200 = MCTSAgent(num_rounds=200)
_mcts_400 = MCTSAgent(num_rounds=400)
_mcts_800 = MCTSAgent(num_rounds=800)


def mcts_agent(game_state):
    return _mcts_400.select_move(game_state)


def mcts_100(game_state):
    return _mcts_100.select_move(game_state)


def mcts_200(game_state):
    return _mcts_200.select_move(game_state)


def mcts_400(game_state):
    return _mcts_400.select_move(game_state)


def mcts_800(game_state):
    return _mcts_800.select_move(game_state)


# =========================
# Minimax Agents（不同depth）
# =========================
from agents.minimax_agent import MinimaxAgent

_minimax_d2 = MinimaxAgent(max_depth=2)
_minimax_d3 = MinimaxAgent(max_depth=3)
_minimax_d4 = MinimaxAgent(max_depth=4)
_minimax_d5 = MinimaxAgent(max_depth=5)


def minimax_agent(game_state):
    return _minimax_d3.select_move(game_state)


def minimax_d2(game_state):
    return _minimax_d2.select_move(game_state)


def minimax_d3(game_state):
    return _minimax_d3.select_move(game_state)


def minimax_d4(game_state):
    return _minimax_d4.select_move(game_state)


def minimax_d5(game_state):
    return _minimax_d5.select_move(game_state)

# Agent Registry
AGENTS = {
    "random": random_agent,

    "mcts": mcts_agent,
    "mcts_100": mcts_100,
    "mcts_200": mcts_200,
    "mcts_400": mcts_400,
    "mcts_800": mcts_800,

    "minimax": minimax_agent,
    "minimax_d2": minimax_d2,
    "minimax_d3": minimax_d3,
    "minimax_d4": minimax_d4,
    "minimax_d5": minimax_d5,
}


# Board Print
def print_board(game_state):
    board = game_state.board

    print("  ", end="")
    for c in range(1, board.num_cols + 1):
        print(f"{c:2}", end="")
    print()

    for r in range(1, board.num_rows + 1):
        print(f"{r:2}", end="")
        for c in range(1, board.num_cols + 1):
            stone = board.get(Point(r, c))
            if stone == Player.black:
                print(" X", end="")
            elif stone == Player.white:
                print(" O", end="")
            else:
                print(" .", end="")
        print()

# Game Loop
def play_game(agent1_fn, agent2_fn, board_size=5, verbose=True):
    game = GameState.new_game(board_size)

    agents = {
        Player.black: agent1_fn,
        Player.white: agent2_fn,
    }

    move_count = 0
    start_time = time.time()

    while not game.is_over():

        if verbose:
            print(f"\n=== Move {move_count + 1}, {game.next_player.name} ===")
            print_board(game)

        agent_fn = agents[game.next_player]
        move = agent_fn(game)

        # 防止 None 崩溃
        if move is None:
            move = Move.pass_turn()

        if verbose:
            print(f"选择: {move}")

        game = game.apply_move(move)
        move_count += 1

        if move_count > board_size * board_size * 2:
            print("[WARN] 步数过多，强制结束")
            break

    duration = time.time() - start_time
    winner = game.winner()

    if verbose:
        print("\n=== 终局 ===")
        print_board(game)
        print("胜者:", winner.name if winner else "平局")

    return winner, move_count, duration


# CLI
def main():
    parser = argparse.ArgumentParser(description="Go AI Play")

    parser.add_argument("--agent1", choices=AGENTS.keys(), default="random")
    parser.add_argument("--agent2", choices=AGENTS.keys(), default="random")
    parser.add_argument("--size", type=int, default=5)
    parser.add_argument("--games", type=int, default=1)
    parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args()

    agent1 = AGENTS[args.agent1]
    agent2 = AGENTS[args.agent2]

    results = {Player.black: 0, Player.white: 0, None: 0}
    total_moves = 0
    total_time = 0

    for i in range(args.games):
        if not args.quiet:
            print(f"\n========== Game {i+1}/{args.games} ==========")

        winner, moves, duration = play_game(
            agent1, agent2, args.size, verbose=not args.quiet
        )

        results[winner] += 1
        total_moves += moves
        total_time += duration

    print("\n========== Statistics ==========")
    print(f"Games: {args.games}")
    print(f"Black ({args.agent1}) wins: {results[Player.black]}")
    print(f"White ({args.agent2}) wins: {results[Player.white]}")
    print(f"Draws: {results[None]}")
    print(f"Avg moves: {total_moves / args.games:.1f}")
    print(f"Avg time: {total_time / args.games:.2f}s")


if __name__ == "__main__":
    main()