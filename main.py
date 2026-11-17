import chess
import chess.engine
import random

class TinyBeast:
    def __init__(self):
        self.board = chess.Board()

    def evaluate(self):
        values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        score = 0
        for piece_type, value in values.items():
            score += len(self.board.pieces(piece_type, chess.WHITE)) * value
            score -= len(self.board.pieces(piece_type, chess.BLACK)) * value

        return score if self.board.turn else -score

    def choose_move(self):
        moves = list(self.board.legal_moves)

        if not moves:
            return None

        best_move = None
        best_score = -float("inf")

        for move in moves:
            self.board.push(move)
            score = -self.evaluate()
            self.board.pop()

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

if __name__ == "__main__":
    engine = TinyBeast()

    while not engine.board.is_game_over():
        move = engine.choose_move()
        if move is None:
            break

        print("Tiny Beast:", move)
        engine.board.push(move)