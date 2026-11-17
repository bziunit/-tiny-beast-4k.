import chess
import chess.polyglot

class TinyBeast:
    def __init__(self, depth=4):
        self.depth = depth

    def evaluate(self, board):
        if board.is_checkmate():
            return -100000 if board.turn else 100000

        if board.is_stalemate():
            return 0

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
            score += len(board.pieces(piece_type, True)) * value
            score -= len(board.pieces(piece_type, False)) * value

        return score if board.turn else -score

    def search(self, board, depth, alpha, beta):
        if depth == 0 or board.is_game_over():
            return self.evaluate(board), None

        best_move = None
        best_score = -float("inf")

        for move in board.legal_moves:
            board.push(move)
            score = -self.search(
                board, depth - 1, -beta, -alpha
            )[0]
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score, best_move

    def get_move(self, board):
        return self.search(
            board, self.depth,
            -float("inf"), float("inf")
        )[1]


if __name__ == "__main__":
    board = chess.Board()
    engine = TinyBeast(depth=4)

    move = engine.get_move(board)
    print("Tiny Beast 4K:", move)