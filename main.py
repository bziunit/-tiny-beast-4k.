
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
            white = len(self.board.pieces(piece, chess.WHITE))
            black = len(self.board.pieces(piece, chess.BLACK))
            score += (white - black) * value

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)

            if piece is None:
                continue

            file = chess.square_file(square)
            rank = chess.square_rank(square)

            center = 7 - (
                abs(3.5 - file) + abs(3.5 - rank)
            )

            bonus = int(center * 8)

            if piece.piece_type == chess.PAWN:
                advancement = (
                    rank if piece.color == chess.WHITE
                    else 7 - rank
                )
                bonus += advancement * 5

            if piece.piece_type == chess.KNIGHT:
                bonus += int(center * 5)

            if piece.piece_type == chess.BISHOP:
                bonus += int(center * 3)

            score += bonus if piece.color else -bonus

        return score if self.board.turn else -score

    def move_score(self, move):
        score = 0

        if self.board.is_capture(move):
            victim = self.board.piece_at(move.to_square)

            if victim is None and self.board.is_en_passant(move):
                score += 100

            elif victim is not None:
                score += (
                    10 * PIECE_VALUES[victim.piece_type]
                    - PIECE_VALUES[self.board.piece_at(
                        move.from_square
                    ).piece_type]
                )

        if move.promotion:
            score += PIECE_VALUES[move.promotion]

        return score

    def alphabeta(self, depth, alpha, beta):
        self.nodes += 1

        if depth == 0 or self.board.is_game_over():
            return self.evaluate()

        best = -float("inf")

        moves = sorted(
            self.board.legal_moves,
            key=self.move_score,
            reverse=True
        )

        for move in moves:
            self.board.push(move)
            score = -self.alphabeta(
                depth - 1, -beta, -alpha
            )
            self.board.pop()

            best = max(best, score)
            alpha = max(alpha, score)

            if alpha >= beta:
                break

        return best

         def choose_move(self):
        best_move = None
        self.nodes = 0

        for current_depth in range(1, self.depth + 1):
            best_score = -float("inf")
            alpha = -float("inf")
            beta = float("inf")

            moves = sorted(
                self.board.legal_moves,
                key=self.move_score,
                reverse=True
            )

            for move in moves:
                self.board.push(move)

                score = -self.alphabeta(
                    current_depth - 1,
                    -beta,
                    -alpha
                )

                self.board.pop()

                if score > best_score:
                    best_score = score
                    best_move = move

                alpha = max(alpha, score)

        return best_move