
import chess
import sys
import time

NAME = "Tiny Beast"
MATE = 100000
INF = 1000000

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
        self.time_limit = None
        self.stopped = False

    def evaluate(self, board):
        if board.is_checkmate():
            return -MATE
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0

        for square, piece in board.piece_map().items():
            value = VALUES[piece.piece_type]
            file = chess.square_file(square)
            rank = chess.square_rank(square)

            center = 7 - (
                abs(3.5 - file) + abs(3.5 - rank)
            )

            if piece.piece_type == chess.PAWN:
                advance = rank if piece.color else 7 - rank
                value += advance * 8
                value += int(center * 3)

            elif piece.piece_type == chess.KNIGHT:
                value += int(center * 9)

            elif piece.piece_type == chess.BISHOP:
                value += int(center * 5)

            elif piece.piece_type == chess.ROOK:
                value += int(center * 2)

            elif piece.piece_type == chess.QUEEN:
                value += int(center * 2)

            elif piece.piece_type == chess.KING:
                if len(board.piece_map()) <= 12:
                    value += int(center * 10)
                else:
                    value -= int(center * 5)

            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value

        score += (
            len(board.legal_moves) * 2
            if board.turn == chess.WHITE
            else -len(board.legal_moves) * 2
        )

        return score if board.turn == chess.WHITE else -score

    def move_score(self, board, move, tt_move=None):
        if move == tt_move:
            return 1000000

        score = 0

        if move.promotion:
            score += 80000 + VALUES[move.promotion]

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)

            victim_value = (
                VALUES[victim.piece_type] if victim else 100
            )
            attacker_value = (
                VALUES[attacker.piece_type] if attacker else 0
            )

            score += 50000 + victim_value * 10 - attacker_value

        return score

    def ordered_moves(self, board, tt_move=None):
        return sorted(
            list(board.legal_moves),
            key=lambda move: self.move_score(
                board, move, tt_move
            ),
            reverse=True
        )

    def time_check(self):
        if self.time_limit is None:
            return False

        if time.time() - self.start_time >= self.time_limit:
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

        if qply >= 8:
            return self.evaluate(board)

        in_check = board.is_check()

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
            moves = list(board.legal_moves)

        moves.sort(
            key=lambda move: self.move_score(board, move),
            reverse=True
        )

        for move in moves:
            board.push(move)
            score = -self.quiescence(
                board, -beta, -alpha, ply + 1, qply + 1
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
            return self.quiescence(board, alpha, beta, ply)

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

        moves = self.ordered_moves(board, tt_move)

        if not moves:
            return -MATE + ply if board.is_check() else 0

        for move in moves:
            board.push(move)
            score = -self.search(
                board, depth - 1, -beta, -alpha, ply + 1
            )
            board.pop()

            if self.stopped:
                return 0

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

            if alpha >= beta:
                break

        if best_score <= original_alpha:
            flag = "UPPER"
        elif best_score >= beta:
            flag = "LOWER"
        else:
            flag = "EXACT"

        self.tt[key] = (
            depth, best_score, flag, best_move
        )

        if len(self.tt) > 200000:
            self.tt.clear()

        return best_score

    def best_move(self, board, depth=4, movetime=None):
        self.nodes = 0
        self.start_time = time.time()
        self.time_limit = movetime
        self.stopped = False

        legal = list(board.legal_moves)

        if not legal:
            return None

        best = legal[0]

        for current_depth in range(1, max(1, depth) + 1):
            self.stopped = False
            self.nodes = 0

            score = self.search(
                board, current_depth, -INF, INF
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

            if self.time_limit is not None:
                if time.time() - self.start_time >= self.time_limit:
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

        elif cmd == "position":
            try:
                if len(parts) >= 2 and parts[1] == "startpos":
                    board = chess.Board()
                    move_start = 2

                elif len(parts) >= 2 and parts[1] == "fen":
                    fen_end = parts.index("moves") if "moves" in parts else len(parts)
                    fen = " ".join(parts[2:fen_end])
                    board = chess.Board(fen)
                    move_start = fen_end

                else:
                    continue

                if move_start < len(parts) and parts[move_start] == "moves":
                    for move_text in parts[move_start + 1:]:
                        move = chess.Move.from_uci(move_text)
                        if move in board.legal_moves:
                            board.push(move)

            except (ValueError, IndexError):
                board = chess.Board()

        elif cmd == "go":
            depth = 4
            movetime = None

            if "depth" in parts:
                try:
                    depth = int(parts[parts.index("depth") + 1])
                except (ValueError, IndexError):
                    depth = 4

            if "movetime" in parts:
                try:
                    movetime = int(
                        parts[parts.index("movetime") + 1]
                    ) / 1000
                except (ValueError, IndexError):
                    movetime = None

            move = engine.best_move(
                board, depth=depth, movetime=movetime
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
        move = engine.best_move(board, depth=4)
        print(move)
