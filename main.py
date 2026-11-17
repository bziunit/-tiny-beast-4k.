
import chess
import sys
import time

# Tiny Beast 4K — improved endgame and search

INF = 1000000
MATE = 100000
MAX_PLY = 96

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
        self.killers = [[None, None] for _ in range(MAX_PLY)]
        self.history = {}
        self.nodes = 0

    def evaluate(self, board):
        """Evaluation from White's point of view."""
        score = 0
        endgame = (
            len(board.pieces(chess.QUEEN, chess.WHITE))
            + len(board.pieces(chess.QUEEN, chess.BLACK)) == 0
            or sum(
                VALUES[piece.piece_type]
                for piece in board.piece_map().values()
                if piece.piece_type != chess.KING
            ) <= 2600
        )

        for square, piece in board.piece_map().items():
            color_sign = 1 if piece.color == chess.WHITE else -1
            file_index = chess.square_file(square)
            rank_index = chess.square_rank(square)

            relative_rank = (
                rank_index if piece.color == chess.WHITE
                else 7 - rank_index
            )

            center = 7 - (
                abs(2 * file_index - 7)
                + abs(2 * rank_index - 7)
            ) / 2

            value = VALUES[piece.piece_type]

            if piece.piece_type == chess.PAWN:
                value += relative_rank * 9
                value += center * 2

                # Passed pawns become especially dangerous in endgames.
                passed = True
                for enemy_square in board.pieces(
                    chess.PAWN, not piece.color
                ):
                    enemy_file = chess.square_file(enemy_square)
                    enemy_rank = chess.square_rank(enemy_square)

                    if abs(enemy_file - file_index) <= 1:
                        if piece.color == chess.WHITE:
                            if enemy_rank > rank_index:
                                passed = False
                        else:
                            if enemy_rank < rank_index:
                                passed = False

                if passed:
                    value += (relative_rank ** 2) * (
                        3 if endgame else 2
                    )

            elif piece.piece_type == chess.KNIGHT:
                value += center * 8

            elif piece.piece_type == chess.BISHOP:
                value += center * 5

            elif piece.piece_type == chess.ROOK:
                if relative_rank == 6:
                    value += 22

                # Open and semi-open files.
                own_pawns = any(
                    chess.square_file(s) == file_index
                    for s in board.pieces(chess.PAWN, piece.color)
                )
                enemy_pawns = any(
                    chess.square_file(s) == file_index
                    for s in board.pieces(chess.PAWN, not piece.color)
                )
                if not own_pawns:
                    value += 12 if not enemy_pawns else 6

            elif piece.piece_type == chess.QUEEN:
                value += center * 2

            elif piece.piece_type == chess.KING:
                if endgame:
                    value += center * 10
                    value += relative_rank * 3
                else:
                    # Keep the king safer during the middlegame.
                    value -= center * 5

            score += color_sign * value

        return int(score)

    def is_draw(self, board):
        return (
            board.is_insufficient_material()
            or board.is_fifty_moves()
            or board.is_repetition(3)
        )

    def move_score(self, board, move, ply, tt_move=None):
        if tt_move is not None and move == tt_move:
            return 2_000_000

        if move.promotion:
            return 1_000_000 + VALUES[move.promotion]

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)

            victim_value = (
                VALUES[victim.piece_type] if victim else VALUES[chess.PAWN]
            )
            attacker_value = (
                VALUES[attacker.piece_type] if attacker else 0
            )

            return 900_000 + victim_value * 10 - attacker_value

        if ply < MAX_PLY:
            if move == self.killers[ply][0]:
                return 800_000
            if move == self.killers[ply][1]:
                return 700_000

        return self.history.get(
            (board.turn, move.from_square, move.to_square), 0
        )

    def ordered_moves(self, board, moves, ply, tt_move=None):
        return sorted(
            moves,
            key=lambda move: self.move_score(
                board, move, ply, tt_move
            ),
            reverse=True,
        )

    def quiescence(self, board, alpha, beta, ply, qply=0):
        self.nodes += 1

        if self.is_draw(board):
            return 0

        in_check = board.is_check()

        if not in_check:
            stand_pat = self.evaluate(board)
            if board.turn == chess.BLACK:
                stand_pat = -stand_pat

            if stand_pat >= beta:
                return beta

            if stand_pat > alpha:
                alpha = stand_pat

            if qply >= 12:
                return alpha

            moves = [
                move for move in board.legal_moves
                if board.is_capture(move) or move.promotion
            ]
        else:
            # In check, search every legal escape.
            if qply >= 12:
                return -MATE + ply

            moves = list(board.legal_moves)
            if not moves:
                return -MATE + ply

        moves = self.ordered_moves(board, moves, ply)

        for move in moves:
            board.push(move)
            score = -self.quiescence(
                board, -beta, -alpha, ply + 1, qply + 1
            )
            board.pop()

            if score >= beta:
                return beta

            if score > alpha:
                alpha = score

        return alpha

    def search(self, board, depth, alpha, beta, ply=0):
        self.nodes += 1

        if self.is_draw(board):
            return 0, None

        if ply >= MAX_PLY - 1:
            score = self.evaluate(board)
            return (score if board.turn else -score), None

        if board.is_checkmate():
            return -MATE + ply, None

        if depth <= 0:
            return self.quiescence(board, alpha, beta, ply), None

        original_alpha = alpha
        key = board.fen()
        tt_entry = self.tt.get(key)
        tt_move = None

        if tt_entry:
            tt_depth, tt_score, tt_flag, tt_best = tt_entry
            tt_move = tt_best

            if tt_depth >= depth:
                if tt_flag == "EXACT":
                    return tt_score, tt_best
                if tt_flag == "LOWER" and tt_score >= beta:
                    return tt_score, tt_best
                if tt_flag == "UPPER" and tt_score <= alpha:
                    return tt_score, tt_best

        moves = list(board.legal_moves)

        if not moves:
            return (-MATE + ply if board.is_check() else 0), None

        moves = self.ordered_moves(board, moves, ply, tt_move)
        best_move = None
        best_score = -INF

        for move in moves:
            board.push(move)
            score, _ = self.search(
                board, depth - 1, -beta, -alpha, ply + 1
            )
            score = -score
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                if not board.is_capture(move) and ply < MAX_PLY:
                    if move != self.killers[ply][0]:
                        self.killers[ply][1] = self.killers[ply][0]
                        self.killers[ply][0] = move

                    hist_key = (
                        board.turn, move.from_square, move.to_square
                    )
                    self.history[hist_key] = (
                        self.history.get(hist_key, 0) + depth * depth
                    )
                break

        flag = "EXACT"
        if best_score <= original_alpha:
            flag = "UPPER"
        elif best_score >= beta:
            flag = "LOWER"

        self.tt[key] = (
            depth, best_score, flag, best_move
        )

        return best_score, best_move

    def choose_move(self, board, max_depth=4):
        self.nodes = 0

        if board.is_game_over():
            return None

        best_move = None

        # Iterative deepening: keep the best move from the last
        # completed search depth.
        for depth in range(1, max_depth + 1):
            _, move = self.search(board, depth, -INF, INF)

            if move is not None:
                best_move = move

        return best_move


def uci_loop():
    engine = TinyBeast()
    board = chess.Board()

    print("id name Tiny Beast 4K", flush=True)
    print("id author Tiny Beast", flush=True)
    print("uciok", flush=True)

    while True:
        try:
            command = input().strip()
        except EOFError:
            break

        if not command:
            continue

        parts = command.split()
        name = parts[0]

        if name == "uci":
            print("id name Tiny Beast 4K", flush=True)
            print("id author Tiny Beast", flush=True)
            print("uciok", flush=True)

        elif name == "isready":
            print("readyok", flush=True)

        elif name == "ucinewgame":
            engine = TinyBeast()
            board = chess.Board()

        elif name == "position":
            try:
                if len(parts) >= 2 and parts[1] == "startpos":
                    board = chess.Board()
                    move_start = 2

                elif len(parts) >= 2 and parts[1] == "fen":
                    try:
                        move_start = parts.index("moves")
                        fen = " ".join(parts[2:move_start])
                    except ValueError:
                        fen = " ".join(parts[2:])
                        move_start = len(parts)

                    board = chess.Board(fen)

                else:
                    continue

                if move_start < len(parts) and parts[move_start] == "moves":
                    for move_text in parts[move_start + 1:]:
                        board.push_uci(move_text)

            except (ValueError, IndexError):
                board = chess.Board()

        elif name == "go":
            depth = 4

            if "depth" in parts:
                try:
                    depth = int(parts[parts.index("depth") + 1])
                except (ValueError, IndexError):
                    depth = 4

            depth = max(1, min(depth, 12))
            move = engine.choose_move(board, depth)

            if move is None:
                print("bestmove 0000", flush=True)
            else:
                print("bestmove", move.uci(), flush=True)

        elif name == "stop":
            continue

        elif name == "quit":
            break


if __name__ == "__main__":
    if "--uci" in sys.argv:
        uci_loop()
    else:
        engine = TinyBeast()
        board = chess.Board()
        move = engine.choose_move(board, 4)
        print(move.uci() if move else "No legal move")
