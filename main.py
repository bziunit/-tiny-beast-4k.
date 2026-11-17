
import chess
import sys

MATE = 100000
INF = 1000000

VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 950,
    chess.KING: 0,
}

class TinyBeast:
    def __init__(self):
        self.tt = {}
        self.nodes = 0
        self.killers = {}
        self.history = {}

    def evaluate(self):
        board = self.board
        score = 0

        for square, piece in board.piece_map().items():
            color = 1 if piece.color == chess.WHITE else -1
            file = chess.square_file(square)
            rank = chess.square_rank(square)

            relative_rank = rank if color == 1 else 7 - rank
            center = 7 - (
                abs(2 * file - 7) + abs(2 * rank - 7)
            ) / 2

            value = VALUES[piece.piece_type]

            if piece.piece_type == chess.PAWN:
                value += relative_rank * 8
                value += center * 2

            elif piece.piece_type == chess.KNIGHT:
                value += center * 9

            elif piece.piece_type == chess.BISHOP:
                value += center * 5

            elif piece.piece_type == chess.ROOK:
                value += relative_rank * 2

            elif piece.piece_type == chess.QUEEN:
                value += center * 2

            elif piece.piece_type == chess.KING:
                if board.fullmove_number < 25:
                    value -= center * 7
                else:
                    value += center * 8

            score += color * value

        score += 10 * (
            len(list(board.legal_moves))
            if board.turn == chess.WHITE else
            -len(list(board.legal_moves))
        )

        return score if board.turn == chess.WHITE else -score

    def move_score(self, move, tt_move=None, ply=0):
        board = self.board

        if move == tt_move:
            return 10000000

        score = 0

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)

            if board.is_en_passant(move):
                victim_value = VALUES[chess.PAWN]
            else:
                victim_value = VALUES[victim.piece_type] if victim else 0

            attacker = board.piece_at(move.from_square)
            attacker_value = VALUES[attacker.piece_type]

            score += 100000 + victim_value * 10 - attacker_value

        if move.promotion:
            score += 90000 + VALUES[move.promotion]

        if board.gives_check(move):
            score += 500

        if move in self.killers.get(ply, []):
            score += 30000

        score += self.history.get(
            (board.turn, move.from_square, move.to_square), 0
        )

        return score

    def ordered_moves(self, moves, tt_move=None, ply=0):
        return sorted(
            moves,
            key=lambda move: self.move_score(move, tt_move, ply),
            reverse=True
        )

    def quiescence(self, alpha, beta, ply=0, qdepth=0):
        self.nodes += 1

        if self.board.is_checkmate():
            return -MATE + ply

        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0

        if self.board.is_fifty_moves() or self.board.is_repetition(3):
            return 0

        in_check = self.board.is_check()

        if not in_check:
            stand_pat = self.evaluate()

            if stand_pat >= beta:
                return beta

            if stand_pat > alpha:
                alpha = stand_pat

            if qdepth >= 12:
                return alpha

            moves = [
                move for move in self.board.legal_moves
                if self.board.is_capture(move) or move.promotion
            ]
        else:
            moves = list(self.board.legal_moves)

        moves = self.ordered_moves(moves, ply=ply)

        if in_check and not moves:
            return -MATE + ply

        for move in moves:
            self.board.push(move)
            score = -self.quiescence(
                -beta, -alpha, ply + 1, qdepth + 1
            )
            self.board.pop()

            if score >= beta:
                return beta

            if score > alpha:
                alpha = score

        return alpha

    def alphabeta(self, depth, alpha, beta, ply=0):
        self.nodes += 1

        if self.board.is_checkmate():
            return -MATE + ply

        if (
            self.board.is_stalemate()
            or self.board.is_insufficient_material()
            or self.board.is_fifty_moves()
            or self.board.is_repetition(3)
        ):
            return 0

        if depth <= 0:
            return self.quiescence(alpha, beta, ply)

        original_alpha = alpha
        key = self.board.fen()
        entry = self.tt.get(key)
        tt_move = None

        if entry:
            tt_move = entry[1]
            stored_depth, stored_move, stored_score, flag = entry

            if stored_depth >= depth:
                if flag == "EXACT":
                    return stored_score
                if flag == "LOWER" and stored_score >= beta:
                    return stored_score
                if flag == "UPPER" and stored_score <= alpha:
                    return stored_score

        moves = self.ordered_moves(
            list(self.board.legal_moves), tt_move, ply
        )

        best_score = -INF
        best_move = None

        for move in moves:
            self.board.push(move)
            score = -self.alphabeta(
                depth - 1, -beta, -alpha, ply + 1
            )
            self.board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                if not self.board.is_capture(move):
                    killers = self.killers.setdefault(ply, [])
                    if move not in killers:
                        killers.insert(0, move)
                    self.killers[ply] = killers[:2]

                    hist_key = (
                        self.board.turn,
                        move.from_square,
                        move.to_square
                    )
                    self.history[hist_key] = (
                        self.history.get(hist_key, 0) + depth * depth
                    )
                break

        if best_score <= original_alpha:
            flag = "UPPER"
        elif best_score >= beta:
            flag = "LOWER"
        else:
            flag = "EXACT"

        self.tt[key] = (depth, best_move, best_score, flag)

        if len(self.tt) > 200000:
            self.tt.clear()

        return best_score

    def choose_move(self, board, depth=4):
        self.board = board.copy()
        self.nodes = 0

        best_move = None

        for current_depth in range(1, depth + 1):
            alpha = -INF
            beta = INF
            best_score = -INF

            moves = self.ordered_moves(
                list(self.board.legal_moves)
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

                if score > alpha:
                    alpha = score

        return best_move


def uci_loop():
    engine = TinyBeast()
    board = chess.Board()

    while True:
        try:
            line = input().strip()
        except EOFError:
            break

        if not line:
            continue

        tokens = line.split()
        command = tokens[0]

        if command == "uci":
            print("id name Tiny Beast 4K")
            print("id author Tiny Beast")
            print("uciok")
            sys.stdout.flush()

        elif command == "isready":
            print("readyok")
            sys.stdout.flush()

        elif command == "ucinewgame":
            engine.tt.clear()
            engine.killers.clear()
            engine.history.clear()
            board = chess.Board()

        elif command == "position":
            try:
                if tokens[1] == "startpos":
                    board = chess.Board()
                    move_index = 2

                elif tokens[1] == "fen":
                    move_index = tokens.index("moves") if "moves" in tokens else len(tokens)
                    fen = " ".join(tokens[2:move_index])
                    board = chess.Board(fen)

                else:
                    continue

                if "moves" in tokens:
                    start = tokens.index("moves") + 1
                    for move_text in tokens[start:]:
                        move = chess.Move.from_uci(move_text)
                        if move in board.legal_moves:
                            board.push(move)

            except (ValueError, IndexError):
                print("info string Invalid position")
                sys.stdout.flush()

        elif command == "go":
            depth = 4

            if "depth" in tokens:
                try:
                    depth = int(tokens[tokens.index("depth") + 1])
                except (ValueError, IndexError):
                    depth = 4

            depth = max(1, min(depth, 12))

            move = engine.choose_move(board, depth)

            if move is None:
                print("bestmove 0000")
            else:
                print("bestmove", move.uci())

            sys.stdout.flush()

        elif command == "stop":
            continue

        elif command == "quit":
            break


if __name__ == "__main__":
    if "--uci" in sys.argv:
        uci_loop()
    else:
        engine = TinyBeast()
        board = chess.Board()
        move = engine.choose_move(board, 4)
        print("Best move:", move)
        print("Nodes:", engine.nodes)
