
import chess
import chess.engine

from main import TinyBeast


MOVE_TIME = 0.75
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
        "French — po Qh5+",
        """
        e4 e6 d4 d5 Nc3 Nf6 e5 Nfd7 Nf3 Nc6
        Bd3 f6 Bf4 g5 Nxg5 Nxd4 Qh5+
        """
    ),
    (
        "Queen's Gambit — przed Qg4#",
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
        Kxf3 f5 Kf4 Qe4+
        """
    ),
    (
        "English — przed h6#",
        """
        c4 e5 Nc3 Nf6 g3 d5
        d4 exd4 Qxd4 Nc6 Qd3 Nb4
        Qe3+ Be6 Qd2 dxc4 Nf3 Qxd2+
        Kxd2 Rd8+ Nd4 Rxd4+ Ke3 Nc2+
        Kf3 Nxa1 Be3 Nc2 Bxd4 Nxd4+
        Ke3 Bc5 f3 Nf5+ Kf4 Bd6+
        """
    ),
    (
        "Reti — przed Ne3#",
        """
        Nf3 d5 d4 Nf6 c4 e6
        Nbd2 c5 cxd5 exd5 dxc5 Bxc5
        Qa4+ Nc6 Qb5 Bb6 Ne5 O-O
        Nxc6 bxc6 Qxc6 Ng4 Qxa8 Bxf2+
        """
    ),
    (
        "Reti — przed Rh7#",
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
        Ne5 Qf8 Ndf7+ Kh7 Ng5+
        """
    ),
]


def build_position(name, moves_text):
    board = chess.Board()
    moves = moves_text.split()

    for index, san in enumerate(moves, start=1):
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


def safe_moves(board):
    safe = []

    for move in list(board.legal_moves):
        board.push(move)

        opponent_mates = immediate_mates(board)

        board.pop()

        if not opponent_mates:
            safe.append(move)

    return safe


def test_move(board, move):
    if move is None or move not in board.legal_moves:
        return False, []

    test_board = board.copy()
    test_board.push(move)

    mates = immediate_mates(test_board)

    return not bool(mates), mates


def describe_moves(board, moves):
    if not moves:
        return "brak"

    return ", ".join(
        board.san(move) for move in moves
    )


def main():
    engine = TinyBeast()

    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/usr/games/stockfish"
    )

    try:
        print("========== TINY BEAST TACTICAL DIAGNOSTIC ==========")

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

            tiny_safe, tiny_mates = test_move(
                board,
                tiny_move
            )

            print()
            print("Tiny Beast:")
            print(
                "Ruch:",
                board.san(tiny_move) if tiny_move else "brak"
            )
            print("Bezpieczny:", tiny_safe)
            print(
                "Mat w 1 po ruchu:",
                describe_moves(
                    board,
                    tiny_mates
                )
            )

            sf_result = stockfish.play(
                board,
                chess.engine.Limit(
                    depth=STOCKFISH_DEPTH
                )
            )

            sf_move = sf_result.move

            sf_safe, sf_mates = test_move(
                board,
                sf_move
            )

            print()
            print("Stockfish:")
            print(
                "Ruch:",
                board.san(sf_move) if sf_move else "brak"
            )
            print("Bezpieczny:", sf_safe)
            print(
                "Mat w 1 po ruchu:",
                describe_moves(
                    board,
                    sf_mates
                )
            )

            print()
            print("========================================")

        print()
        print("========== TEST ZAKOŃCZONY ==========")

    finally:
        stockfish.quit()


if __name__ == "__main__":
    main()
