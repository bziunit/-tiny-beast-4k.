import chess
import sys

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}


class TinyBeast:
    def __init__(self, depth=3):
        self.board = chess.Board()
        self.depth = depth
        self.nodes = 0

    def evaluate(self):
        if self.board.is_checkmate():
            return -100000

        if self.board.is_game_over():
            return 0

        score = 0

        for piece, value in PIECE_VALUES.items():
            score += len(self.board.pieces(piece, chess.WHITE)) * value
            score -= len(self.board.pieces(piece, chess.BLACK)) * value

        return score if self.board.turn else -score

    def alphabeta(self, depth, alpha, beta):
        self.nodes += 1

        if depth == 0 or self.board.is_game_over():
            return self.evaluate()

        best = -float("inf")

        for move in self.board.legal_moves:
            self.board.push(move)
            score = -self.alphabeta(depth - 1, -beta, -alpha)
            self.board.pop()

            best = max(best, score)
            alpha = max(alpha, score)

            if alpha >= beta:
                break

        return best

    def choose_move(self):
        best_move = None
        best_score = -float("inf")

        for move in self.board.legal_moves:
            self.board.push(move)
            score = -self.alphabeta(
                self.depth - 1, -float("inf"), float("inf")
            )
            self.board.pop()

            if score > best_score:
                best_score = score
                best_move = move

        return best_move


def uci():
    engine = TinyBeast(depth=3)

    while True:
        command = input().strip()

        if command == "uci":
            print("id name Tiny Beast 4K")
            print("id author Tiny Beast")
            print("uciok", flush=True)

        elif command == "isready":
            print("readyok", flush=True)

        elif command == "ucinewgame":
            engine.board.reset()

        elif command.startswith("position"):
            parts = command.split()
            if "startpos" in parts:
                engine.board.reset()
                if "moves" in parts:
                    idx = parts.index("moves") + 1
                    for move in parts[idx:]:
                        engine.board.push_uci(move)

            elif "fen" in parts:
                idx = parts.index("fen") + 1
                fen_end = parts.index("moves") if "moves" in parts else len(parts)
                engine.board.set_fen(" ".join(parts[idx:fen_end]))
                if "moves" in parts:
                    idx = parts.index("moves") + 1
                    for move in parts[idx:]:
                        engine.board.push_uci(move)

        elif command.startswith("go"):
            move = engine.choose_move()
            if move:
                print("bestmove", move.uci(), flush=True)
            else:
                print("bestmove 0000", flush=True)

        elif command == "quit":
            break


if __name__ == "__main__":
    if "--uci" in sys.argv:
        uci()
    else:
        engine = TinyBeast(depth=3)
        move = engine.choose_move()
        print("Tiny Beast:", move)