
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
        self.tt = {}
        self.killers = {}
        self.history = {}

   
        self.tt.clear()
        self.killers.clear()
        self.history.clear()

        for current_depth in range(1, self.depth + 1):
            best_score = -float("inf")
            alpha = -float("inf")
            beta = float("inf")

            moves = list(self.board.legal_moves)

            moves.sort(
                key=lambda move: self.move_score(move, 0),
                reverse=True
            )

            for move in moves:
                self.board.push(move)

                score = -self.alphabeta(
                    current_depth - 1,
                    -beta,
                    -alpha,
                    1
                )

                self.board.pop()

                if score > best_score:
                    best_score = score
                    best_move = move

                alpha = max(alpha, score)

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
            engine.tt.clear()
            engine.killers.clear()
            engine.history.clear()

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

                fen_end = (
                    parts.index("moves")
                    if "moves" in parts else len(parts)
                )

                engine.board.set_fen(
                    " ".join(parts[idx:fen_end])
                )

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
        print("Nodes:", engine.nodes)
        print("Zapamiętane pozycje:", len(engine.tt))

    def evaluate(self):
        if self.board.is_checkmate():
            return -100000

        if self.board.is_game_over():
            return 0

        score = 0

        # Material and piece activity
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
                    rank if piece.color else 7 - rank
                )
                bonus += advancement * 5

            if piece.piece_type == chess.KNIGHT:
                bonus += int(center * 5)

            if piece.piece_type == chess.BISHOP:
                bonus += int(center * 3)

            score += bonus if piece.color else -bonus

        # Pawn structure and king safety
        for color in (chess.WHITE, chess.BLACK):
            sign = 1 if color else -1
            pawns = list(self.board.pieces(chess.PAWN, color))
            files = [chess.square_file(sq) for sq in pawns]

            # Doubled and isolated pawns
            for file in range(8):
                count = files.count(file)

                if count > 1:
                    score -= sign * 15 * (count - 1)

                if count > 0:
                    has_neighbor = (
                        file > 0 and (file - 1) in files
                    ) or (
                        file < 7 and (file + 1) in files
                    )

                    if not has_neighbor:
                        score -= sign * 12 * count

            # King pawn shield
            king_square = self.board.king(color)

            if king_square is not None:
                king_file = chess.square_file(king_square)
                king_rank = chess.square_rank(king_square)

                shield_rank = (
                    king_rank + 1 if color
                    else king_rank - 1
                )

                if 0 <= shield_rank < 8:
                    for f in range(
                        max(0, king_file - 1),
                        min(7, king_file + 1) + 1
                    ):
                        shield_square = chess.square(
                            f, shield_rank
                        )

                        if self.board.piece_at(shield_square) == chess.Piece(
                            chess.PAWN, color
                        ):
                            score += sign * 18

        return score if self.board.turn else -score
