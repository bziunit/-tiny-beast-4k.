
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

    def move_score(self, move, ply, tt_move=None):
        if move == tt_move:
            return 10000000

        if self.board.is_capture(move):
            victim = self.board.piece_at(move.to_square)

            if victim is None and self.board.is_en_passant(move):
                victim_value = PIECE_VALUES[chess.PAWN]
            elif victim is not None:
                victim_value = PIECE_VALUES[victim.piece_type]
            else:
                victim_value = 0

            attacker = self.board.piece_at(move.from_square)
            attacker_value = PIECE_VALUES[attacker.piece_type]

            return 1000000 + 10 * victim_value - attacker_value

        if move.promotion:
            return 900000 + PIECE_VALUES[move.promotion]

        killer_moves = self.killers.get(ply, [])

        if move in killer_moves:
            return 800000 - killer_moves.index(move)

        return self.history.get(
            (self.board.turn, move.from_square, move.to_square),
            0
        )

    def quiescence(self, alpha, beta, ply=0):
        self.nodes += 1

        if self.board.is_checkmate():
            return -100000 + ply

        if self.board.is_game_over():
            return 0

        in_check = self.board.is_check()

        if not in_check:
            stand_pat = self.evaluate()

            if stand_pat >= beta:
                return beta

            alpha = max(alpha, stand_pat)

            moves = [
                move for move in self.board.legal_moves
                if self.board.is_capture(move) or move.promotion
            ]
        else:
            moves = list(self.board.legal_moves)

        moves.sort(
            key=lambda move: self.move_score(move, ply),
            reverse=True
        )

        for move in moves:
            self.board.push(move)

            score = -self.quiescence(
                -beta,
                -alpha,
                ply + 1
            )

            self.board.pop()

            if score >= beta:
                return beta

            alpha = max(alpha, score)

        return alpha

    def alphabeta(self, depth, alpha, beta, ply=0):
        self.nodes += 1

        if self.board.is_game_over():
            return self.evaluate()

        if depth <= 0:
            return self.quiescence(alpha, beta, ply)

        original_alpha = alpha
        original_beta = beta

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
            key=lambda move: self.move_score(
                move, ply, tt_move
            ),
            reverse=True
        )

        best = -float("inf")
        best_move = None

        for move in moves:
            is_capture = self.board.is_capture(move)
            moving_color = self.board.turn

            self.board.push(move)

            score = -self.alphabeta(
                depth - 1,
                -beta,
                -alpha,
                ply + 1
            )

            self.board.pop()

            if score > best:
                best = score
                best_move = move

            alpha = max(alpha, score)

            if alpha >= beta:
                if not is_capture and not move.promotion:
                    killers = self.killers.setdefault(ply, [])

                    if move not in killers:
                        killers.insert(0, move)
                        if len(killers) > 2:
                            killers.pop()

                    history_key = (
                        moving_color,
                        move.from_square,
                        move.to_square
                    )

                    self.history[history_key] = (
                        self.history.get(history_key, 0)
                        + depth * depth
                    )

                break

        if best <= original_alpha:
            flag = "UPPER"
        elif best >= original_beta:
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
