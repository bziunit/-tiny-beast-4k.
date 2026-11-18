
import chess
import chess.engine

from main import TinyBeast


TINY_TIME = 1.5
STOCKFISH_DEPTH = 14
STOCKFISH_PATH = "/usr/games/stockfish"

POSITIONS = [
    (
        "SYCYLIJSKA — przed 19.Nc6",
        """
        e4 c5 Nf3 d6 d4 cxd4 Nxd4 a6
        Nc3 Nf6 Bc4 e6 O-O Qc7 Be2 Be7
        f4 O-O Be3 b5 a4 b4 Na2 Bb7
        b3 Nxe4 Nxb4 Bf6 c4 Nd7 f5
        Ndc5 Kh1 Nc3 Nxe6 fxe6
        """,
        "Nc6",
    ),
    (
        "RETI — przed 20.Qc8",
        """
        Nf3 d5 d4 Nf6 c4 e6 Nbd2 c5
        h4 cxd4 Nxd4 e5 N4f3 e4 Ne5
        e3 fxe3 Bd6 Ndf3 Nc6 Nxc6 bxc6
        Qa4 Bg3+ Kd1 O-O Qxc6 dxc4+
        Nd4 Bd7 Qxc4 Qa5 Bd2 Qh5
        Be1 Ng4 Ne6 Bxe6
        """,
        "Qc8",
    ),
]


def build_position(name, moves_text):
    board = chess.Board()

    for number, san in enumerate(moves_text.split(), start=1):
        try:
            board.push_san(san)
        except ValueError as error:
            raise ValueError(
                f"{name}: nielegalny ruch {number}: {san}; "
                f"FEN: {board.fen()}"
            ) from error

    return board


def score_cp(info, color):
    return info["score"].pov(color).score(
        mate_score=100000
    )


def show_line(board, moves, limit=10):
    position = board.copy()
    result = []

    for move in moves[:limit]:
        result.append(position.san(move))
        position.push(move)

    return " ".join(result)


def analyze_position(tiny, stockfish, name, moves_text, old_move):
    board = build_position(name, moves_text)
    color = board.turn

    print("\n" + "=" * 65)
    print(name)
    print("=" * 65)
    print("FEN:", board.fen())
    print("Na ruchu:", "White" if color else "Black")
    print("Historyczny ruch:", old_move)

    old = board.parse_san(old_move)

    tiny_move = tiny.best_move(
        board.copy(),
        depth=4,
        movetime=TINY_TIME
    )

    if tiny_move is None:
        print("Tiny Beast nie podał ruchu.")
        return

    print("\nTiny Beast:", board.san(tiny_move))

    lines = stockfish.analyse(
        board,
        chess.engine.Limit(depth=STOCKFISH_DEPTH),
        multipv=3
    )

    print("\nNajlepsze ruchy Stockfish:")

    for number, info in enumerate(lines, start=1):
        pv = info.get("pv", [])
        if not pv:
            continue

        print(
            f"{number}. {board.san(pv[0])} "
            f"| ocena: {score_cp(info, color)} cp "
            f"| wariant: {show_line(board, pv)}"
        )

    tiny_info = stockfish.analyse(
        board,
        chess.engine.Limit(depth=STOCKFISH_DEPTH),
        root_moves=[tiny_move]
    )

    old_info = stockfish.analyse(
        board,
        chess.engine.Limit(depth=STOCKFISH_DEPTH),
        root_moves=[old]
    )

    best_score = score_cp(lines[0], color)
    tiny_score = score_cp(tiny_info, color)
    old_score = score_cp(old_info, color)

    print("\nPorównanie:")
    print("Najlepsza ocena Stockfish:", best_score, "cp")
    print("Ocena ruchu Tiny Beast:", tiny_score, "cp")
    print("Ocena starego ruchu:", old_score, "cp")
    print("Strata ruchu Tiny Beast:", best_score - tiny_score, "cp")
    print("Strata starego ruchu:", best_score - old_score, "cp")

    print("\nWynik:")
    if tiny_score > old_score + 50:
        print("NOWY WYBÓR JEST LEPSZY OD HISTORYCZNEGO.")
    elif tiny_score < old_score - 50:
        print("NOWY WYBÓR JEST GORSZY OD HISTORYCZNEGO.")
    else:
        print("Brak wyraźnej różnicy.")

    print("\nTEST POZYCJI ZAKOŃCZONY")


def main():
    tiny = TinyBeast()

    stockfish = chess.engine.SimpleEngine.popen_uci(
        STOCKFISH_PATH
    )

    try:
        print("========== TEST BEZPIECZEŃSTWA FIGUR ==========")

        for position in POSITIONS:
            analyze_position(tiny, stockfish, *position)

        print("\n========== TEST ZAKOŃCZONY ==========")

    finally:
        stockfish.quit()


if __name__ == "__main__":
    main()
