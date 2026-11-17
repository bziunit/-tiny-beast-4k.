
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
                    rank if piece.color else 7 - rank
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
                attacker = self.board.piece_at(move.from_square)
                score += (
                    10 * PIECE_VALUES[victim.piece_type]
                    - PIECE_VALUES[attacker.piece_type]
                )

        if move.promotion:
            score += PIECE_VALUES[move.promotion]

        return score

    def alphabeta(self, depth, alpha, beta):
        self.nodes += 1

        if depth == 0 or self.board.is_game_over():
            return self.evaluate()

        original_alpha = alpha
        key = self.board.fen()

        entry = self.tt.get(key)
        tt_move = None

        if entry is not None:
            stored_depth, stored_score, flag, stored_move = entry

            if stored_move is not None:
                tt_move = chess.Move.from_uci(stored_move)

            if stored_depth >= depth:
                if flag == "EXACT":
                    return stored_score
                elif flag == "LOWER":
                    alpha = max(alpha, stored_score)
                elif flag == "UPPER":
                    beta = min(beta, stored_score)

                if alpha >= beta:
                    return stored_score

        moves = list(self.board.legal_moves)

        moves.sort(
            key=self.move_score,
            reverse=True
        )

        if tt_move in moves:
            moves.remove(tt_move)
            moves.insert(0, tt_move)

        best = -float("inf")
        best_move = None

        for move in moves:
            self.board.push(move)

            score = -self.alphabeta(
                depth - 1,
                -beta,
                -alpha
            )

            self.board.pop()

            if score > best:
                best = score
                best_move = move

            alpha = max(alpha, score)

            if alpha >= beta:
                break

        if best <= original_alpha:
            flag = "UPPER"
        elif best >= beta:
            flag = "LOWER"
        else:
            flag = "EXACT"

        self.tt[key] = (
            depth,
            best,
            flag,
            best_move.uci() if best_move else None
        )

        return best

    def choose_move(self):
        best_move = None
        self.nodes = 0
        self.tt.clear()

        for current_depth in range(1, self.depth + 1):
            best_score = -float("inf")
            alpha = -float("inf")
            beta = float("inf")

            moves = list(self.board.legal_moves)
            moves.sort(
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
