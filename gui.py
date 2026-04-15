import tkinter as tk
from tkinter import messagebox
import threading
import queue

from dlgo.gotypes import Player, Point
from dlgo.goboard import GameState, Move

from agents.random_agent import RandomAgent
from agents.mcts_agent import MCTSAgent

try:
    from agents.minimax_agent import MinimaxAgent
except:
    MinimaxAgent = None


class GoGUI:
    def __init__(self, size=5):
        self.size = size
        self.cell = 60
        self.offset = 40

        self.root = tk.Tk()
        self.root.title("AI围棋对弈")

        # ================= 游戏状态 =================
        self.game = GameState.new_game(size)
        self.history = []

        self.pass_count = 0
        self.ai_thinking = False

        # ================= AI类型 =================
        self.ai_type = tk.StringVar(value="mcts")

        # ✔ 只创建一次AI
        self.agent = self.create_agent()

        # ================= UI =================
        self.build_ui()

        # ================= 线程队列 =================
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()

        self.worker = threading.Thread(target=self.ai_worker, daemon=True)
        self.worker.start()

        self.draw()
        self.root.mainloop()

    # ================= 创建AI =================
    def create_agent(self):
        t = self.ai_type.get()

        if t == "random":
            return RandomAgent()

        elif t == "mcts":
            return MCTSAgent(num_rounds=200)   # 固定200 rounds

        elif t == "minimax" and MinimaxAgent:
            return MinimaxAgent()

        return RandomAgent()

    # ================= UI =================
    def build_ui(self):
        top = tk.Frame(self.root)
        top.pack()

        tk.Label(top, text="AI选择:").pack(side=tk.LEFT)

        tk.OptionMenu(
            top,
            self.ai_type,
            "random",
            "mcts",
            "minimax",
            command=self.change_ai
        ).pack(side=tk.LEFT)

        tk.Button(top, text="新游戏", command=self.new_game).pack(side=tk.LEFT)
        tk.Button(top, text="悔棋", command=self.undo).pack(side=tk.LEFT)

        self.label = tk.Label(self.root, font=("Arial", 12))
        self.label.pack()

        self.canvas = tk.Canvas(
            self.root,
            width=self.size * self.cell + self.offset,
            height=self.size * self.cell + self.offset,
            bg="#DDBB77"
        )
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self.click)

    # ================= 切换AI =================
    def change_ai(self, _=None):
        self.agent = self.create_agent()

    # ================= AI线程 =================
    def ai_worker(self):
        while True:
            state = self.task_queue.get()

            move = self.agent.select_move(state)

            self.result_queue.put((state, move))

    # ================= 人类落子 =================
    def click(self, event):
        if self.ai_thinking or self.game.is_over():
            return

        c = round((event.x - self.offset) / self.cell) + 1
        r = round((event.y - self.offset) / self.cell) + 1

        if not (1 <= r <= self.size and 1 <= c <= self.size):
            return

        move = Move.play(Point(r, c))

        if not self.game.is_valid_move(move):
            print("非法落子")
            return

        self.history.append(self.game)
        self.game = self.game.apply_move(move)

        self.pass_count = 0
        self.draw()

        self.start_ai()

    # ================= 启动AI =================
    def start_ai(self):
        self.ai_thinking = True
        self.label.config(text="AI思考中...")

        self.task_queue.put(self.game)

        self.root.after(50, self.check_ai)

    # ================= 获取AI结果 =================
    def check_ai(self):
        try:
            state, move = self.result_queue.get_nowait()
        except queue.Empty:
            self.root.after(50, self.check_ai)
            return

        # 防止旧状态污染
        if state != self.game:
            self.ai_thinking = False
            return

        self.history.append(self.game)
        self.game = self.game.apply_move(move)

        if move.is_pass:
            self.pass_count += 1
        else:
            self.pass_count = 0

        self.ai_thinking = False

        self.draw()

        # ================= 终局 =================
        if self.game.is_over() or self.pass_count >= 2:
            self.end_game()
            return

        # AI只走一步，不会连下
        self.label.config(text="轮到你下")

    # ================= 画棋盘 =================
    def draw(self):
        self.canvas.delete("all")

        # grid
        for i in range(self.size):
            self.canvas.create_line(
                self.offset, self.offset + i * self.cell,
                self.offset + (self.size - 1) * self.cell,
                self.offset + i * self.cell
            )
            self.canvas.create_line(
                self.offset + i * self.cell, self.offset,
                self.offset + i * self.cell,
                self.offset + (self.size - 1) * self.cell
            )

        black = 0
        white = 0

        for r in range(1, self.size + 1):
            for c in range(1, self.size + 1):
                stone = self.game.board.get(Point(r, c))

                if stone == Player.black:
                    black += 1
                elif stone == Player.white:
                    white += 1

                if stone:
                    color = "black" if stone == Player.black else "white"

                    x = self.offset + (c - 1) * self.cell
                    y = self.offset + (r - 1) * self.cell

                    self.canvas.create_oval(
                        x - 20, y - 20,
                        x + 20, y + 20,
                        fill=color
                    )

        self.label.config(
            text=f"回合: {self.game.next_player.name} | 黑:{black} 白:{white}"
        )

    # ================= 终局 =================
    def end_game(self):
        winner = self.game.winner()

        black = sum(
            1 for r in range(1, self.size + 1)
            for c in range(1, self.size + 1)
            if self.game.board.get(Point(r, c)) == Player.black
        )

        white = sum(
            1 for r in range(1, self.size + 1)
            for c in range(1, self.size + 1)
            if self.game.board.get(Point(r, c)) == Player.white
        )

        if winner == Player.black:
            msg = f"黑胜 {black} vs {white}"
        elif winner == Player.white:
            msg = f"白胜 {white} vs {black}"
        else:
            msg = f"平局 {black} vs {white}"

        messagebox.showinfo("终局", msg)

    # ================= 新游戏 =================
    def new_game(self):
        self.game = GameState.new_game(self.size)
        self.history = []
        self.pass_count = 0
        self.ai_thinking = False
        self.draw()

    # ================= 悔棋 =================
    def undo(self):
        if self.history:
            self.game = self.history.pop()
            self.ai_thinking = False
            self.draw()


if __name__ == "__main__":
    GoGUI()