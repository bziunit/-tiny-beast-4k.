import chess
import chess.engine
import time

from main import TinyBeast


MOVE_TIME = 3.0
STOCKFISH_DEPTH = 12

POSITIONS = [
    (
        "RUY LOPEZ — przed 33...Ka8",
        """
        e4 e5 Nf3 Nc6 Bb5 a6
        Bc4 b5 Bd5 Nge7 O-O Nxd5 exd5 Ne7
        d4 e4 Ng5 h6 Nxe4 Nxd5 Re1 Be7
        Qf3 Nb4 Qg3 Nxc2 Qxg7 Nxe1 Qxh8+ Bf8
        Bxh6 Nf3+ gxf3 Qe7 Nbd2 f5 Ng5 c6
        h4 a5 Rc1 f4 Nde4 Qb4 Kg2 Ba6 Qg8 O-O-O
        Ne6 dxe6 Bxf4 Kb7 Qxe6 Qxd4 Qxc6+ Ka7
        Qc7+ Bb7 Qxa5+ Ba6 Be3 Rd7 Bxd4+ Rxd4
        Rc7+
        """
    ),
    (
        "SICILIAN — przed 44...Kd7",
        """
        e4 c5 Nf3 d6 d4 cxd4 Nxd4 e5 Nb5 a6
        Bg5 f6 Be3 axb5 Qh5+ g6 Bxb5+ Nc6 Qf3 Be6
        Nc3 h5 Nd5 Ra5 Bb6 Qxb6 Nxb6 Rxb5
        Nd5 Rxb2 Qc3 Bxd5 exd5 Rb6 dxc6 bxc6
        O-O Ne7 Rfb1 Rxb1+ Rxb1 Kd7 Qa3 g5
        Rb7+ Ke6 Qb3+ Nd5 a4 c5 a5 f5 Rb8 Bg7
        Rb5 Bf6 a6 Ra8 Qa4 Nc3 Qc4+ Nd5 Rb3 e4
        Rb7 Bd4 g3 Ke5 Qa4 g4 a7 f4 gxf4+ Kxf4
        Kh1 Bxf2 Rf7+ Ke5 Qd7 e3 Qf5+ Kd4
        Qd3+ Ke5 Rf5+ Ke6 Qxd5+
        """
    ),
    (
        "QUEEN'S GAMBIT — przed 93.Kd4",
        """
        d4 d5 c4 e6 Nc3 Nf6 cxd5 exd5 Nf3 Be7
        Ne5 O-O Be3 Re8 Rc1 c6 h4 Nbd7 g3 Nxe5
        dxe5 Ng4 Bd4 c5 Be3 d4 Bf4 dxc3 Qxd8 Bxd8
        Rxc3 Ba5 a4 Nxe5 Bxe5 Rxe5 Kd2 Kh8 b3 Be6
        f4 Re4 Kc2 c4 Rxc4 Bxc4 bxc4 Rd8 Rg1 Re6
        Kb3 Re3+ Kb2 h5 g4 Rd2+ Kb1 Rd1+ Kc2 Rd8
        gxh5 Rc3+ Kb2 Rd2+ Kb1 Rd1+ Ka2 Rd2+ Kb1 Rd8
        e4 Rd1+ Kb2 Rd2+ Kb1 Rd1+ Kb2 Rcc1 Rg4 Bc3+
        Kb3 Rd2 c5 Rb2+ Kc4 Ba5+ Kd4 Bc3+ Kd3 Rd2+
        Ke3 Re1+ Kf3 Bd4 Rg5 Rxf1+ Kg4 Rg1+ Kf5 Rxg5+
        hxg5 Bxc5 g6 Kg8 e5 Kf8 gxf7 Kxf7 e6+ Ke7
        Ke5 Bd6+ Ke4 Rb2 f5 a5 h6 gxh6 Kd5 Bb8 Kd4 Bd6
        Kd5 Bb8 Kd4 Bg3 Ke3 Bd6 Kd4 Rf2 Ke4 Rf4+
        Ke3 Rxf5 Ke4 Re5+ Kd3 Rf5 Ke4 Rf4+ Kd5 Rf8
        Ke4 h5 Kd4 Bb4 Ke5 Bc3+ Ke4 Bg7 Kd3 Kxe6
        Ke3 Rf6 Ke4 Bf8 Ke3 Bh6+ Kd3 Ke7 Kc4 h4
        Kc5 h3 Kb5 h2 Kxa5 b6+ Kb5 h1=Q Kc4 Qe4+
        Kb3 Qb1+ Kc4 Qc2+ Kb4 Qb2+ Kc4 Rc6+ Kd5 Rc5+
        Ke4 Qe2+
        """
    ),
    (
        "RETI — przed 39...Kd7",
        """
        Nf3 d5 d4 Nf6 c4 e6 e3 Nbd7 Nc3 c5 Be2 cxd4
        exd4 dxc4 Bxc4 Nb6 Ne5 Nxc4 Nxc4 Bd6 Qa4+ Kf8
        Nxd6 Qxd6 b3 Qc6 Qxc6 bxc6 Ba3+ Kg8 Kd2 Ba6
        Bc5 h5 h4 g6 Be7 Nd7 Ne4 Nb6 Bf6 Rh6 Rac1 Rc8
        a4 Nd5 Bg5 Rh7 Nf6+ Nxf6 Bxf6 Kf8 Rc5 Bb7
        b4 Ke8 Re1 Kd7 Ke3 a6 f3 Rb8 Rb1 Rh6
        Ke4 Bc8 Ke5 Rb6 g3 Rb7 Rbc1 Rxb4 Rxc6 Rb6
        Rc7+ Ke8 Rxc8+
        """
    ),
]


def build_position(name, moves_text):
    board = chess.Board()

    for index, san in enumerate(moves_text.split(), start=1):
        try:
            move = board.parse_san(san)
            board.push(move)
        except ValueError as error:
            raise ValueError(
                f"{name}: nielegalny ruch nr {index}: {san}. "
                f"FEN przed błędem: {board.fen()}"
            ) from error

    return board


def immediate_mates(board):
    mates = []

    for move in list(board.legal_moves):
        board.push(move)

        if board.is_checkmate():
            mates.append(move)

        board.pop()

    return mates


def forced_mate_in_two(board):
    forced = []

    for opponent_move in list(board.legal_moves):
        board.push(opponent_move)

        if board.is_checkmate():
            forced.append(opponent_move)
            board.pop()
            continue

        replies = list(board.legal_moves)

        if not replies:
            board.pop()
            continue

        every_reply_loses = True

        for reply in replies:
            board.push(reply)

            if board.is_checkmate():
                every_reply_loses = False
                board.pop()
                break

            opponent_mates = immediate_mates(board)
            board.pop()

            if not opponent_mates:
                every_reply_loses = False
                break

        board.pop()

        if every_reply_loses:
            forced.append(opponent_move)

    return forced


def analyze_move(board, move):
    if move is None or move not in board.legal_moves:
        return False, [], []

    test_board = board.copy()
    test_board.push(move)

    mates_one = immediate_mates(test_board)
    mates_two = forced_mate_in_two(test_board)

    return not mates_one and not mates_two, mates_one, mates_two


def safe_moves(board):
    result = []

    for move in list(board.legal_moves):
        safe, _, _ = analyze_move(board, move)

        if safe:
            result.append(move)

    return result


def describe_moves(board, moves):
    if not moves:
        return "brak"

    return ", ".join(board.san(move) for move in moves)


def describe_replies_after(board, move, replies):
    if not replies:
        return "brak"

    position = board.copy()
    position.push(move)

    return ", ".join(position.san(reply) for reply in replies)


def report_move(board, label, move):
    print()
    print(label)

    if move is None:
        print("Ruch: brak")
        return

    print("Ruch:", board.san(move))

    safe, mates_one, mates_two = analyze_move(board, move)

    after = board.copy()
    after.push(move)

    print("Bezpieczny według diagnostyki:", safe)
    print(
        "Mat w 1 po tym ruchu:",
        describe_moves(after, mates_one)
    )
    print(
        "Ruchy przeciwnika wymuszające mata w 2:",
        describe_replies_after(board, move, mates_two)
    )


def main():
    tiny = TinyBeast()

    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/usr/games/stockfish"
    )

    try:
        print("========== DIAGNOSTYKA CZTERECH PRZEGRANYCH ==========")

        for name, moves_text in POSITIONS:
            print()
            print("=" * 60)
            print(name)
            print("=" * 60)

            board = build_position(name, moves_text)

            print("FEN:", board.fen())
            print(
                "Na ruchu:",
                "White" if board.turn == chess.WHITE else "Black"
            )
            print("Król w szachu:", board.is_check())
            print("Legalne ruchy:", len(list(board.legal_moves)))

            start = time.perf_counter()
            safe = safe_moves(board)
            elapsed = time.perf_counter() - start

            print("Bezpieczne ruchy:", len(safe))
            print("Lista bezpiecznych:", describe_moves(board, safe))
            print(f"Czas filtra diagnostycznego: {elapsed:.3f} s")

            tiny_move = tiny.best_move(
                board.copy(),
                depth=4,
                movetime=MOVE_TIME
            )

            report_move(board, "TINY BEAST", tiny_move)

            sf_result = stockfish.play(
                board,
                chess.engine.Limit(depth=STOCKFISH_DEPTH)
            )

            report_move(board, "STOCKFISH", sf_result.move)

        print()
        print("========== DIAGNOSTYKA ZAKOŃCZONA ==========")

    finally:
        stockfish.quit()


if __name__ == "__main__":
    main()