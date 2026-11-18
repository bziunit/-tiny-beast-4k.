
import chess
import chess.engine

from main import TinyBeast

MOVE_TIME = 3.0
STOCKFISH_DEPTH = 18

MOVES = """
e4 e5 Nf3 Nc6 Bb5 a6
Bc4 b5 Bd5 Nge7 O-O Nxd5 exd5 Ne7
d4 e4 Ng5 h6 Nxe4 Nxd5 Re1 Be7
"""

def main():
    board = chess.Board()

    for san in MOVES.split():
        board.push_san(san)

    print("===== POZYCJA PRZED 12.Qf3 =====")
    print("FEN:", board.fen())
    print("Legalne ruchy:", board.legal_moves.count())

    tiny = TinyBeast()
    tiny_move = tiny.best_move(
        board.copy(),
        depth=4,
        movetime=MOVE_TIME
    )

    print("\n===== TINY BEAST =====")
    print("Wybrany ruch:", board.san(tiny_move))

    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/usr/games/stockfish"
    )

    try:
        print("\n===== STOCKFISH TOP 5 =====")

        lines = stockfish.analyse(
            board,
            chess.engine.Limit(depth=STOCKFISH_DEPTH),
            multipv=5
        )

        for number, info in enumerate(lines, 1):
            move = info["pv"][0]
            score = info["score"].pov(chess.WHITE).score(
                mate_score=100000
            )
            print(
                f"{number}. {board.san(move)} "
                f"| {score} cp"
            )

        print("\n===== PORÓWNANIE =====")
        tiny_san = board.san(tiny_move)
        top_moves = [board.san(info["pv"][0]) for info in lines]

        print("Tiny Beast:", tiny_san)
        print("Czy ruch jest w TOP 5:", tiny_san in top_moves)

        if tiny_san in top_moves:
            print("Pozycja w TOP 5:", top_moves.index(tiny_san) + 1)

        print("\n===== TEST ZAKOŃCZONY =====")

    finally:
        stockfish.quit()


if __name__ == "__main__":
    main()
