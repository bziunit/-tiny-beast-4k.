
import time
import chess
from main import TinyBeast


def benchmark():
    engine = TinyBeast(depth=3)

    positions = [
        chess.STARTING_FEN,
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        "r3k2r/ppp2ppp/2n1bn2/3qp3/3P4/2N1PN2/PPP2PPP/R2QKB1R w KQkq - 0 1",
    ]

    total_nodes = 0
    total_time = 0.0

    print("TINY BEAST 4K BENCHMARK")
    print("-----------------------")

    for number, fen in enumerate(positions, 1):
        engine.board.set_fen(fen)

        start = time.perf_counter()
        move = engine.choose_move()
        elapsed = time.perf_counter() - start

        nodes = engine.nodes
        total_nodes += nodes
        total_time += elapsed

        print(f"\nPosition: {number}")
        print("Best move:", move)
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
