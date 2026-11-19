
import chess
import chess.engine

from main import TinyBeast

FEN = "r2qkbnr/1p6/2npbpp1/1B1Np2p/4P3/4BQ2/PPP2PPP/R3K2R b KQkq - 1 12"
STOCKFISH_PATH = "/usr/games/stockfish"


def show_score(score):
    mate = score.mate()
    if mate is not None:
        return f"MAT w {mate} ruchach" if mate > 0 else f"MAT za {abs(mate)} ruchów"
    return f"{score.score():+d} cp"


def main():
    board = chess.Board(FEN)

    print("===== SYCYLIJSKA: DIAGNOSTYKA RUCHU 12 =====")
    print("Pozycja:")
    print(board)
    print("\nFEN:", board.fen())
    print("Na ruchu:", "White" if board.turn else "Black")

    tiny = TinyBeast()
    print("\nUruchamiam Tiny Beast...")
    tiny_move = tiny.best_move(board, depth=4, movetime=2.0)

    if tiny_move:
        print("Tiny Beast wybrał:", board.san(tiny_move))
        print("UCI:", tiny_move.uci())
    else:
        print("Tiny Beast nie zwrócił ruchu.")

    print("\nUruchamiam Stockfisha...")
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    try:
        engine.configure({"Threads": 1, "Hash": 256})
        results = engine.analyse(
            board,
            chess.engine.Limit(depth=14),
            multipv=10
        )

        print("\n===== TOP 10 STOCKFISHA =====")
        for index, info in enumerate(results, start=1):
            move = info["pv"][0]
            score = info["score"].pov(chess.BLACK)
            print(
                f"{index}. {board.san(move):8} "
                f"{show_score(score):>18} "
                f"głębokość: {info['depth']}"
            )

        print("\n===== PORÓWNANIE KLUCZOWYCH RUCHÓW =====")
        for san in ("Ra5", "Kf7"):
            try:
                move = board.parse_san(san)
                child = board.copy()
                child.push(move)

                info = engine.analyse(
                    child,
                    chess.engine.Limit(depth=14)
                )
                score = -info["score"].pov(chess.WHITE)

                print(
                    f"{san}: ocena dla czarnych: "
                    f"{show_score(score)}"
                )
                print("  Wariant:", " ".join(
                    chess.Board(FEN).variation_san(info["pv"])
                ) if info.get("pv") else "brak")
            except ValueError:
                print(san, "- ruch nielegalny")

    finally:
        engine.quit()

    print("\n===== DIAGNOSTYKA ZAKOŃCZONA =====")


if __name__ == "__main__":
    main()
