
import chess
import chess.engine

from main import TinyBeast


MOVE_TIME = 3.0
STOCKFISH_DEPTH = 10

POSITIONS = [
    (
        "French — przed Nxd4",
        """
        e4 e6 d4 d5 Nc3 Nf6 e5 Nfd7 Nf3 Nc6
        Bd3 f6 Bf4 g5 Nxg5
        """
    ),
    (
        "Queen's Gambit — przed Kf4",
        """
        d4 d5 c4 e6 Nc3 Nf6
        cxd5 exd5 Nf3 Be7 Qa4+ c6
        Bf4 O-O Bxb8 Rxb8 Qxa7 Bg4
        Ne5 Bb4 h3 Be6 a3 Bxc3+ bxc3 Ne4
        Rb1 Qh4 g3 Qf6 Rh2 Nxc3 Rxb7 Rxb7
        Qxb7 c5 e3 cxd4 exd4 Rc8 Bd3 Ne4
        Bxe4 dxe4 Qxe4 Qd8 Qd3 Qa5+
        Kf1 Rc1+ Kg2 Qe1 Nf3 Bd5
        h4 Rc3 Qf5 Bxf3+ Qxf3 Rxf3
        Kxf3 f5
        """
    ),
    (
        "English — przed Kf4",
        """
        c4 e5 Nc3 Nf6 g3 d5
        d4 exd4 Qxd4 Nc6 Qd3 Nb4
        Qe3+ Be6 Qd2 dxc4 Nf3 Qxd2+
        Kxd2 Rd8+ Nd4 Rxd4+ Ke3 Nc2+
        Kf3 Nxa1 Be3 Nc2 Bxd4 Nxd4+
        Ke3 Bc5 f3 Nf5+
        """
    ),
    (
        "Reti — przed Qxa8",
        """
        Nf3 d5 d4 Nf6 c4 e6
        Nbd2 c5 cxd5 exd5 dxc5 Bxc5
        Qa4+ Nc6 Qb5 Bb6 Ne5 O-O
        Nxc6 bxc6 Qxc6 Ng4
        """
    ),
    (
        "Reti — przed Qf8",
        """
        Nf3 d5 d4 Nf6 c4 e6
        e3 Nbd7 Nc3 c5 Be2 cxd4
        exd4 Bd6 c5 Be7 b4 a5 b5 O-O
        O-O Qc7 b6 Nxb6 Nb5 Qd8
        cxb6 Qxb6 a4 Ne4 Bd3 f5
        Rb1 Ra6 Ne5 Kh8 Bf4 g5
        Bd2 Nxd2 Qxd2 g4 Rfc1 Qd8
        g3 Bg5 Qe1 Bxc1 Qxc1 b6
        h4 gxh3 Qf4 Qe8 Rc1 h5
        Rc7 Qd8 Kh2 Qf6 Nd6 Ra8
        Kxh3 Ba6 Kg2 Bxd3 Nxd3 Rg8
        Ne5
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
                f"{name}: nielegalny ruch nr {index}: "
                f"{san}. Pozycja: {board.fen()}"
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
    """
    Szuka ruchów przeciwnika, po których każda legalna
    odpowiedź prowadzi do mata w następnym ruchu.
    """
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

            # Jeśli nasza odpowiedź sama daje mata,
            # przeciwnik nie ma wymuszonego mata.
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

    safe = not mates_one and not mates_two

    return safe, mates_one, mates_two


def safe_moves(board):
    safe = []

    for move in list(board.legal_moves):
        is_safe, _, _ = analyze_move(board, move)

        if is_safe:
            safe.append(move)

    return safe


def describe_moves(board, moves):
    if not moves:
        return "brak"

    return ", ".join(board.san(move) for move in moves)


def report_move(board, label, move):
    print()
    print(label)

    if move is None:
        print("Ruch: brak")
        return

    print("Ruch:", board.san(move))

    is_safe, mates_one, mates_two = analyze_move(board, move)

    print("Bezpieczny:", is_safe)
    print(
        "Mat w 1 po ruchu:",
        describe_moves(board.copy(stack=False), mates_one)
    )
    print(
        "Ruchy przeciwnika wymuszające mata w 2:",
        describe_moves(board.copy(stack=False), mates_two)
    )


def main():
    engine = TinyBeast()

    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/usr/games/stockfish"
    )

    try:
        print("========== TINY BEAST TACTICAL TEST 2 ==========")

        for name, moves_text in POSITIONS:
            print()
            print("========================================")
            print(name)
            print("========================================")

            board = build_position(name, moves_text)

            print("FEN:", board.fen())
            print(
                "Na ruchu:",
                "White" if board.turn == chess.WHITE else "Black"
            )

            legal = list(board.legal_moves)
            safe = safe_moves(board)

            print("Legalne ruchy:", len(legal))
            print("Bezpieczne ruchy:", len(safe))
            print(
                "Lista bezpiecznych:",
                describe_moves(board, safe)
            )

            tiny_move = engine.best_move(
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
        print("========== TEST ZAKOŃCZONY ==========")

    finally:
        stockfish.quit()


if __name__ == "__main__":
    main()
