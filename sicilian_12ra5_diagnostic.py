
import chess
import chess.engine

from main import TinyBeast

FEN = "r2qkbnr/1p6/2npbpp1/1B1Np2p/4P3/4BQ2/PPP2PPP/R3K2R b KQkq - 1 12"
STOCKFISH_PATH = "/usr/games/stockfish"


def show_score(score):
    mate = score.mate()

    if mate is not None:
        if mate > 0:
            return f"MAT za {mate} ruchów"
        return f"MAT za {abs(mate)} ruchów dla przeciwnika"

    return f"{score.score():+d} cp"


def analyze_move(engine, root, san):
    try:
        move = root.parse_san(san)
    except ValueError:
        print(f"{san}: ruch nielegalny w pozycji początkowej")
        return

    child = root.copy()
    child.push(move)

    info = engine.analyse(
        child,
        chess.engine.Limit(depth=14)
    )

    score = info["score"].pov(chess.BLACK)

    print(f"\n{san} ({move.uci()})")
    print("Ocena dla czarnych:", show_score(score))
    print("Głębokość:", info.get("depth", "?"))

    pv = info.get("pv", [])

    if pv:
        print("Wariant:", child.variation_san(pv))


def main():
    root = chess.Board(FEN)

    print("===== SYCYLIJSKA: DIAGNOSTYKA RUCHU 12 =====")
    print(root)
    print("\nFEN:", root.fen())
    print("Na ruchu:", "White" if root.turn else "Black")

    print("\n===== TINY BEAST =====")

    tiny = TinyBeast()

    # Silnik dostaje kopię, aby nie zmienić pozycji źródłowej.
    tiny_board = root.copy(stack=True)

    tiny_move = tiny.best_move(
        tiny_board,
        depth=4,
        movetime=2.0
    )

    if tiny_move:
        print("Tiny Beast wybrał:", root.san(tiny_move))
        print("UCI:", tiny_move.uci())
    else:
        print("Tiny Beast nie zwrócił ruchu.")

    print("\n===== STOCKFISH =====")

    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    try:
        engine.configure({
            "Threads": 1,
            "Hash": 256
        })

        results = engine.analyse(
            root,
            chess.engine.Limit(depth=14),
            multipv=10
        )

        print("\n===== TOP 10 STOCKFISHA =====")

        for index, info in enumerate(results, start=1):
            move = info["pv"][0]
            score = info["score"].pov(chess.BLACK)

            print(
                f"{index}. {root.san(move):8} "
                f"{show_score(score):>18} "
                f"głębokość: {info['depth']}"
            )

        print("\n===== PORÓWNANIE RUCHÓW =====")

        for san in ("Ra5", "Kf7", "Bxd5"):
            analyze_move(engine, root, san)

    finally:
        engine.quit()

    print("\n===== DIAGNOSTYKA ZAKOŃCZONA =====")


if __name__ == "__main__":
    main()
