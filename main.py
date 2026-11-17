
import chess
import sys

INF = 1_000_000
MATE = 100_000
MAX_PLY = 96

VALUE = {
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
        score = 0
        non_pawn_material = sum(
            VALUE[p.piece_type]
            for p in board.piece_map().values()
            if p.piece_type not in (chess.PAWN, chess.KING)
        )
        endgame = non_pawn_material <= 2600

        for square, piece in board.piece_map().items():
            sign = 1 if piece.color == chess.WHITE else -1
            file_no = chess.square_file(square)
            rank_no = chess.square_rank(square)
            relative_rank = rank_no if piece.color else 7 - rank_no

            center = 7 - (
                abs(2 * file_no - 7) + abs(2 * rank_no - 7)
            ) / 2

            value = VALUE[piece.piece_type]

            if piece.piece_type == chess.PAWN:
                value += relative_rank * 9 + center * 2

                passed = True
                for enemy_sq in board.pieces(
                    chess.PAWN, not piece.color
                ):
                    enemy_file = chess.square_file(enemy_sq)
                    enemy_rank = chess.square_rank(enemy_sq)

                    if abs(enemy_file - file_no) <= 1:
                        if piece.color and enemy_rank > rank_no:
                            passed = False
                        elif not piece.color and enemy_rank < rank_no:
                            passed = False

                if passed:
                    value += relative_rank * relative_rank * (
                        3 if endgame else 2
                    )

            elif piece.piece_type == chess.KNIGHT:
                value += center * 8

            elif piece.piece_type == chess.BISHOP:
                value += center * 5

            elif piece.piece_type == chess.ROOK:
                if relative_rank == 6:
                    value += 22

                own_pawn = any(
                    chess.square_file(s) == file_no
                    for s in board.pieces(chess.PAWN, piece.color)
                )
                enemy_pawn = any(
                    chess.square_file(s) == file_no
                    for s in board.pieces(chess.PAWN, not piece.color)
                )

                if not own_pawn:
                    value += 12 if not enemy_pawn else 6

            elif piece.piece_type == chess.QUEEN:
                value += center * 2

            elif piece.piece_type == chess.KING:
                if endgame:
                    value += center * 10 + relative_rank * 3
                else:
                    value -= center * 5

                    # Small penalty for an exposed king.
                    king_zone = chess.SquareSet(
                        chess.BB_KING_ATTACKS[square]
                    )
                    enemy_attacks = board.attackers(
                        not piece.color, square
                    )
                    value -= len(enemy_attacks) * 12

            score += sign * value

        return int(score)

    def draw(self, board):
        return (
            board.is_insufficient_material()
            or board.is_fifty_moves()
            or board.is_repetition(3)
        )

    def move_order_score(self, board, move, ply, tt_move):
        if move == tt_move:
            return 2_000_000

        if move.promotion:
            return 1_500_000 + VALUE[move.promotion]

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)

            victim_value = VALUE[victim.piece_type] if victim else 100
            attacker_value = VALUE[attacker.piece_type] if attacker else 0

            return 1_000_000 + victim_value * 10 - attacker_value

        if ply < MAX_PLY:
            if move == self.killers[ply][0]:
                return 900_000
            if move == self.killers[ply][1]:
                return 800_000

        key = (board.turn, move.from_square, move.to_square)
        return self.history.get(key, 0)

    def ordered(self, board, moves, ply, tt_move=None):
        return sorted(
            moves,
            key=lambda m: self.move_order_score(
                board, m, ply, tt_move
            ),
            reverse=True,
        )

    def quiescence(self, board, alpha, beta, ply, qply=0):
        self.nodes += 1

        if self.draw(board):
            return 0

        in_check = board.is_check()

        if in_check:
            moves = list(board.legal_moves)

            if not moves:
                return -MATE + ply

        else:
            if board.is_stalemate():
                return 0

            stand_pat = self.evaluate(board)
            if not board.turn:
                stand_pat = -stand_pat

            if stand_pat >= beta:
                return beta

            if stand_pat > alpha:
                alpha = stand_pat

            if qply >= 12:
                return alpha

            moves = [
                m for m in board.legal_moves
                if board.is_capture(m) or m.promotion
            ]

        moves = self.ordered(board, moves, ply)

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

    def search(self, board, depth, alpha, beta, ply=0, extensions=0):
        self.nodes += 1

        if self.draw(board):
            return 0, None

        if board.is_checkmate():
            return -MATE + ply, None

        if ply >= MAX_PLY - 1:
            score = self.evaluate(board)
            return (score if board.turn else -score), None

        in_check = board.is_check()

        # Extend a limited number of checks to avoid missing
        # forced defensive moves and mating attacks.
        if in_check and extensions < 2:
            depth += 1
            extensions += 1

        if depth <= 0:
            return self.quiescence(board, alpha, beta, ply), None

        original_alpha = alpha
        key = board.fen()
        entry = self.tt.get(key)
        tt_move = None

        if entry:
            tt_depth, tt_score, tt_flag, tt_best = entry
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
            return (-MATE + ply if in_check else 0), None

        moves = self.ordered(board, moves, ply, tt_move)
        best_move = None
        best_score = -INF

        for move in moves:
            board.push(move)
            score, _ = self.search(
                board,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
                extensions,
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

                    hkey = (
                        board.turn,
                        move.from_square,
                        move.to_square,
                    )
                    self.history[hkey] = (
                        self.history.get(hkey, 0) + depth * depth
                    )
                break

        flag = "EXACT"
        if best_score <= original_alpha:
            flag = "UPPER"
        elif best_score >= beta:
            flag = "LOWER"

        self.tt[key] = (depth, best_score, flag, best_move)
        return best_score, best_move

    def choose_move(self, board, max_depth=4):
        self.nodes = 0

        if board.is_game_over():
            return None

        best_move = None

        for depth in range(1, max_depth + 1):
            _, move = self.search(board, depth, -INF, INF)

            if move is not None:
                best_move = move

        return best_move


def uci_loop():
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
                if parts[1] == "startpos":
                    board = chess.Board()
                    move_start = 2

                elif parts[1] == "fen":
                    if "moves" in parts:
                        move_start = parts.index("moves")
                        fen = " ".join(parts[2:move_start])
                    else:
                        fen = " ".join(parts[2:])
                        move_start = len(parts)

                    board = chess.Board(fen)

                else:
                    continue

                if (
                    move_start < len(parts)
                    and parts[move_start] == "moves"
                ):
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
