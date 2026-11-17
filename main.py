
import chess
import sys
import time

NAME = "Tiny Beast"
MATE = 100000
INF = 1000000
DEFAULT_MOVE_TIME = 0.75

VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


class TinyBeast:
    def __init__(self):
        self.tt = {}
        self.nodes = 0
        self.start_time = 0
        self.time_limit = DEFAULT_MOVE_TIME
        self.stopped = False

        self.killers = {}
        self.history = {}

    def evaluate(self, board):
        if board.is_checkmate():
            return -MATE

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        pieces = board.piece_map()

        bishops = {
            chess.WHITE: 0,
            chess.BLACK: 0,
        }

        pawn_files = {
            chess.WHITE: [0] * 8,
            chess.BLACK: [0] * 8,
        }

        phase = 0

        for piece in pieces.values():
            if piece.piece_type == chess.QUEEN:
                phase += 4
            elif piece.piece_type == chess.ROOK:
                phase += 2
            elif piece.piece_type in (
                chess.BISHOP,
                chess.KNIGHT
            ):
                phase += 1

        endgame = phase <= 10

        # Material, centrum i aktywność figur
        for square, piece in pieces.items():
            color = piece.color
            sign = 1 if color == chess.WHITE else -1

            value = VALUES[piece.piece_type]

            file = chess.square_file(square)
            rank = chess.square_rank(square)

            center = 7 - (
                abs(3.5 - file) + abs(3.5 - rank)
            )

            advance = rank if color else 7 - rank

            if piece.piece_type == chess.PAWN:
                value += advance * 8
                value += int(center * 3)
                pawn_files[color][file] += 1

            elif piece.piece_type == chess.KNIGHT:
                value += int(center * 10)

            elif piece.piece_type == chess.BISHOP:
                value += int(center * 6)
                bishops[color] += 1

            elif piece.piece_type == chess.ROOK:
                value += int(center * 2)

            elif piece.piece_type == chess.QUEEN:
                value += int(center * 2)

            elif piece.piece_type == chess.KING:
                if endgame:
                    value += int(center * 12)
                else:
                    value -= int(center * 5)

            score += sign * value

        # Struktura pionów i aktywność wież
        for color in (chess.WHITE, chess.BLACK):
            sign = 1 if color == chess.WHITE else -1
            files = pawn_files[color]
            enemy_files = pawn_files[not color]

            for file in range(8):
                if files[file] > 1:
                    score -= sign * 14 * (files[file] - 1)

                if files[file] > 0:
                    left = file > 0 and files[file - 1] > 0
                    right = file < 7 and files[file + 1] > 0

                    if not left and not right:
                        score -= sign * 12 * files[file]

            if bishops[color] >= 2:
                score += sign * 30

            # Wieże na otwartych i półotwartych liniach
            for square in board.pieces(chess.ROOK, color):
                file = chess.square_file(square)
                rank = chess.square_rank(square)

                if files[file] == 0:
                    if enemy_files[file] == 0:
                        score += sign * 20
                    else:
                        score += sign * 12

                if (color and rank == 6) or (
                    not color and rank == 1
                ):
                    score += sign * 15

            # Piony połączone i przechodzące
            own_pawns = board.pieces(chess.PAWN, color)
            enemy_pawns = board.pieces(chess.PAWN, not color)

            for square in own_pawns:
                file = chess.square_file(square)
                rank = chess.square_rank(square)

                connected = False

                for other in own_pawns:
                    if other == square:
                        continue

                    other_file = chess.square_file(other)
                    other_rank = chess.square_rank(other)

                    if (
                        abs(other_file - file) == 1
                        and abs(other_rank - rank) <= 1
                    ):
                        connected = True
                        break

                if connected:
                    score += sign * 8

                passed = True

                for enemy in enemy_pawns:
                    enemy_file = chess.square_file(enemy)
                    enemy_rank = chess.square_rank(enemy)

                    if abs(enemy_file - file) <= 1:
                        if color and enemy_rank > rank:
                            passed = False
                        elif not color and enemy_rank < rank:
                            passed = False

                if passed:
                    bonus = [0, 5, 12, 22, 38, 60, 85, 0]
                    index = rank if color else 7 - rank
                    score += sign * bonus[index]

        # Bezpieczeństwo króla
        for color in (chess.WHITE, chess.BLACK):
            sign = 1 if color == chess.WHITE else -1
            king = board.king(color)

            if king is None:
                continue

            king_file = chess.square_file(king)
            king_rank = chess.square_rank(king)

            if not endgame:
                shield_rank = king_rank + (1 if color else -1)

                if 0 <= shield_rank <= 7:
                    for file in range(
                        max(0, king_file - 1),
                        min(7, king_file + 1) + 1
                    ):
                        shield_square = chess.square(
                            file, shield_rank
                        )

                        if board.piece_at(shield_square) == chess.Piece(
                            chess.PAWN, color
                        ):
                            score += sign * 10

                for file in range(
                    max(0, king_file - 1),
                    min(7, king_file + 1) + 1
                ):
                    if pawn_files[color][file] == 0:
                        score -= sign * 10

                danger = 0

                for df in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if df == 0 and dr == 0:
                            continue

                        f = king_file + df
                        r = king_rank + dr

                        if 0 <= f <= 7 and 0 <= r <= 7:
                            square = chess.square(f, r)

                            if board.is_attacked_by(
                                not color, square
                            ):
                                danger += 1

                score -= sign * min(40, danger * 7)

        # Kary za atakowane i słabo bronione figury
        for square, piece in pieces.items():
            if piece.piece_type == chess.KING:
                continue

            color = piece.color
            sign = 1 if color == chess.WHITE else -1

            attackers = len(
                board.attackers(not color, square)
            )

            defenders = len(
                board.attackers(color, square)
            )

            if attackers > 0:
                value = VALUES[piece.piece_type]

                if defenders == 0:
                    penalty = min(80, int(value * 0.18))
                    score -= sign * penalty

                elif attackers > defenders:
                    penalty = min(55, int(value * 0.10))
                    score -= sign * penalty

        return score if board.turn == chess.WHITE else -score

    def move_score(self, board, move, tt_move=None, ply=0):
        if move == tt_move:
            return 2000000

        score = 0

        if move.promotion:
            score += 1000000 + VALUES[move.promotion]

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)

            if board.is_en_passant(move):
                victim_value = VALUES[chess.PAWN]
            else:
                victim_value = (
                    VALUES[victim.piece_type] if victim else 100
                )

            attacker_value = (
                VALUES[attacker.piece_type] if attacker else 0
            )

            score += (
                500000
                + victim_value * 10
                - attacker_value
            )

            return score

        killers = self.killers.get(ply, [])

        if move in killers:
            score += 400000 - killers.index(move) * 10000

        history_key = (
            board.turn,
            move.from_square,
            move.to_square
        )

        score += self.history.get(history_key, 0)

        return score

    def ordered_moves(self, board, tt_move=None, ply=0):
        return sorted(
            list(board.legal_moves),
            key=lambda move: self.move_score(
                board, move, tt_move, ply
            ),
            reverse=True
        )

    def record_killer(self, move, ply):
        killers = self.killers.setdefault(ply, [])

        if move in killers:
            killers.remove(move)

        killers.insert(0, move)

        if len(killers) > 2:
            killers.pop()

    def record_history(self, board, move, depth):
        key = (
            board.turn,
            move.from_square,
            move.to_square
        )

        self.history[key] = min(
            1000000,
            self.history.get(key, 0) + depth * depth
        )

    def time_check(self):
        if self.time_limit is None:
            return False

        if time.monotonic() - self.start_time >= self.time_limit:
            self.stopped = True
            return True

        return False

    def quiescence(self, board, alpha, beta, ply, qply=0):
        self.nodes += 1

        if self.time_check():
            return self.evaluate(board)

        if board.is_checkmate():
            return -MATE + ply

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        in_check = board.is_check()

        # Limit quiescence nie może przerwać analizy,
        # gdy król jest szachowany.
        if qply >= 8 and not in_check:
            return self.evaluate(board)

        if not in_check:
            stand_pat = self.evaluate(board)

            if stand_pat >= beta:
                return beta

            alpha = max(alpha, stand_pat)

            moves = [
                move for move in board.legal_moves
                if board.is_capture(move) or move.promotion
            ]
        else:
            # W szachu analizujemy wszystkie legalne obrony.
            moves = list(board.legal_moves)

        moves.sort(
            key=lambda move: self.move_score(board, move),
            reverse=True
        )

        for move in moves:
            board.push(move)

            score = -self.quiescence(
                board,
                -beta,
                -alpha,
                ply + 1,
                qply + 1
            )

            board.pop()

            if self.stopped:
                return alpha

            if score >= beta:
                return beta

            alpha = max(alpha, score)

        return alpha

    def search(self, board, depth, alpha, beta, ply=0):
        self.nodes += 1

        if self.time_check():
            return self.evaluate(board)

        if board.is_checkmate():
            return -MATE + ply

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        if board.is_repetition(3):
            return 0

        if depth <= 0:
            return self.quiescence(
                board, alpha, beta, ply
            )

        original_alpha = alpha
        key = board.fen()
        tt_entry = self.tt.get(key)
        tt_move = None

        if tt_entry:
            tt_depth, tt_score, tt_flag, tt_move = tt_entry

            if tt_depth >= depth:
                if tt_flag == "EXACT":
                    return tt_score

                if tt_flag == "LOWER" and tt_score >= beta:
                    return tt_score

                if tt_flag == "UPPER" and tt_score <= alpha:
                    return tt_score

        best_score = -INF
        best_move = None

        moves = self.ordered_moves(board, tt_move, ply)

        if not moves:
            return -MATE + ply if board.is_check() else 0

        for move in moves:
            quiet = (
                not board.is_capture(move)
                and not move.promotion
            )

            board.push(move)

            score = -self.search(
                board,
                depth - 1,
                -beta,
                -alpha,
                ply + 1
            )

            board.pop()

            if self.stopped:
                return 0

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

            if alpha >= beta:
                if quiet:
                    self.record_killer(move, ply)
                    self.record_history(board, move, depth)

                break

        if best_score <= original_alpha:
            flag = "UPPER"
        elif best_score >= beta:
            flag = "LOWER"
        else:
            flag = "EXACT"

        self.tt[key] = (
            depth,
            best_score,
            flag,
            best_move
        )

        if len(self.tt) > 200000:
            self.tt.clear()

        return best_score

    def best_move(self, board, depth=4, movetime=DEFAULT_MOVE_TIME):
        self.nodes = 0
        self.start_time = time.monotonic()
        self.time_limit = movetime
        self.stopped = False

        legal = list(board.legal_moves)

        if not legal:
            return None

        best = legal[0]

        for current_depth in range(1, max(1, depth) + 1):
            if self.time_check():
                break

            self.stopped = False
            self.nodes = 0

            score = self.search(
                board,
                current_depth,
                -INF,
                INF
            )

            if self.stopped:
                break

            entry = self.tt.get(board.fen())

            if entry and entry[3] in legal:
                best = entry[3]

            print(
                "info depth",
                current_depth,
                "score cp",
                score,
                "nodes",
                self.nodes,
                flush=True
            )

            if abs(score) > MATE - 100:
                break

        return best


def uci():
    engine = TinyBeast()
    board = chess.Board()

    while True:
        try:
            command = input().strip()
        except EOFError:
            break

        if not command:
            continue

        parts = command.split()
        cmd = parts[0]

        if cmd == "uci":
            print("id name Tiny Beast", flush=True)
            print("id author Tiny Beast Project", flush=True)
            print("uciok", flush=True)

        elif cmd == "isready":
            print("readyok", flush=True)

        elif cmd == "ucinewgame":
            board = chess.Board()
            engine.tt.clear()
            engine.killers.clear()
            engine.history.clear()

        elif cmd == "position":
            try:
                if len(parts) >= 2 and parts[1] == "startpos":
                    board = chess.Board()
                    move_start = 2

                elif len(parts) >= 2 and parts[1] == "fen":
                    fen_end = (
                        parts.index("moves")
                        if "moves" in parts
                        else len(parts)
                    )

                    fen = " ".join(parts[2:fen_end])
                    board = chess.Board(fen)
                    move_start = fen_end

                else:
                    continue

                if (
                    move_start < len(parts)
                    and parts[move_start] == "moves"
                ):
                    for move_text in parts[move_start + 1:]:
                        move = chess.Move.from_uci(move_text)

                        if move in board.legal_moves:
                            board.push(move)

            except (ValueError, IndexError):
                board = chess.Board()

        elif cmd == "go":
            depth = 4
            movetime = DEFAULT_MOVE_TIME

            if "depth" in parts:
                try:
                    depth = int(
                        parts[parts.index("depth") + 1]
                    )
                except (ValueError, IndexError):
                    depth = 4

            if "movetime" in parts:
                try:
                    movetime = int(
                        parts[parts.index("movetime") + 1]
                    ) / 1000
                except (ValueError, IndexError):
                    movetime = DEFAULT_MOVE_TIME

            move = engine.best_move(
                board,
                depth=depth,
                movetime=movetime
            )

            print(
                "bestmove",
                move.uci() if move else "0000",
                flush=True
            )

        elif cmd == "stop":
            engine.stopped = True

        elif cmd == "quit":
            break


if __name__ == "__main__":
    if "--uci" in sys.argv:
        uci()
    else:
        engine = TinyBeast()
        board = chess.Board()

        move = engine.best_move(
            board,
            depth=4
        )

        print(move)
