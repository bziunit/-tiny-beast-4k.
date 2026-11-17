
import chess
import time

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

class TinyBeast:
    def __init__(self, depth=4):
        self.board = chess.Board()
        self.depth = depth
        self.nodes = 0

    def evaluate(self):
        if self.board.is_checkmate():
            return -100000 + self.board.ply()

        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0

        score = 0

        for piece_type, value in PIECE_VALUES.items():
            score += len(self.board.pieces(piece_type, chess.WHITE)) * value
            score -= len(self.board.pieces(piece_type, chess.BLACK)) * value

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                center = 7 - (
                    abs(3.5 - chess.square_file(square)) +
                    abs(3.5 - chess.square_rank(square))
                )
                bonus = int(center * 8)

                if piece.color == chess.WHITE:
                    score += bonus
                else:
                    score -= bonus

        return score if self.board.turn else -score

    def alphabeta(self, depth, alpha, beta):
        self.nodes += 1

        if depth == 0 or self.board.is_game_over():
            return self.evaluate()

        best = -float("inf")

        moves = sorted(
            self.board.legal_moves,
            key=lambda m: self.board.is_capture(m),
            reverse=True
        )

        for move in moves:
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
        alpha = -float("inf")
        beta = float("inf")

        self.nodes = 0

        for move in self.board.legal_moves:
            self.board.push(move)
            score = -self.alphabeta(
                self.depth - 1, -beta, -alpha
            )
            self.board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        return best_move

if __name__ == "__main__":
    engine = TinyBeast(depth=3)

    for turn in range(10):
        move = engine.choose_move()

        if move is None:
            print("GAME OVER")
            break

        print(f"Move {turn + 1}: {move.uci()}")
        engine.board.push(move)

    print("BOARD AFTER 10 MOVES:")
    print(engine.board)
    print("TINY BEAST TEST FINISHED")