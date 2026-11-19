
import time
import chess
from main import TinyBeast


def benchmark():
    engine = TinyBeast()

    positions = [
        chess.STARTING_FEN,
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        "r3k2r/ppp2ppp/2n1bn2/3qp3/3P4/2N1PN2/PPP2PPP/R2QKB1R w KQkq - 0 1",
    ]

    total_nodes = 0
    total_time = 0.0

    print("TINY BEAST 4K BENCHMARK")
    print("-----------------------")
    print("Search depth: 4")
    print("Move time limit: 5 seconds")

    for number, fen in enumerate(positions, 1):
        board = chess.Board(fen)

        start = time.perf_counter()
        move = engine.best_move(board, depth=4, movetime=5.0)
        elapsed = time.perf_counter() - start

        nodes = engine.nodes
        total_nodes += nodes
        total_time += elapsed

        print(f"\nPosition: {number}")
        print("Best move:", move.uci() if move else "0000")
        print("Nodes:", nodes)
        print("Time:", round(elapsed, 3), "seconds")
        print("Nodes/sec:", int(nodes / elapsed) if elapsed else 0)

    print("\n-----------------------")
    print("TOTAL NODES:", total_nodes)
    print("TOTAL TIME:", round(total_time, 3), "seconds")
    print(
        "AVERAGE NODES/sec:",
        int(total_nodes / total_time) if total_time else 0,
    )


if __name__ == "__main__":
    benchmark()
