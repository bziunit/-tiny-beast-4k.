
import chess
import sys
import time
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}


class TinyBeast:
    def __init__(self, depth=3):
        self.board = chess.Board()
        self.depth = depth
        self.nodes = 0
        self.tt = {}
        self.killers = {}
        self.history = {}

   
        self.tt.clear()
        self.killers.clear()
        self.history.clear()

        for current_depth in range(1, self.depth + 1):
            best_score = -float("inf")
            alpha = -float("inf")
            beta = float("inf")

            moves = list(self.board.legal_moves)

            moves.sort(
                key=lambda move: self.move_score(move, 0),
                reverse=True
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

                alpha = max(alpha, score)

        return best_move


def uci():
    engine = TinyBeast(depth=3)

    while True:
        command = input().strip()

        if command == "uci":
            print("id name Tiny Beast 4K")
            print("id author Tiny Beast")
            print("uciok", flush=True)

        elif command == "isready":
            print("readyok", flush=True)

        elif command == "ucinewgame":
            engine.board.reset()
            engine.tt.clear()
            engine.killers.clear()
            engine.history.clear()

        elif command.startswith("position"):
            parts = command.split()

            if "startpos" in parts:
                engine.board.reset()

                if "moves" in parts:
                    idx = parts.index("moves") + 1
                    for move in parts[idx:]:
                        engine.board.push_uci(move)

            elif "fen" in parts:
                idx = parts.index("fen") + 1

                fen_end = (
                    parts.index("moves")
                    if "moves" in parts else len(parts)
                )

                engine.board.set_fen(
                    " ".join(parts[idx:fen_end])
                )

                if "moves" in parts:
                    idx = parts.index("moves") + 1
                    for move in parts[idx:]:
                        engine.board.push_uci(move)

        elif command.startswith("go"):
            move = engine.choose_move()

            if move:
                print("bestmove", move.uci(), flush=True)
            else:
                print("bestmove 0000", flush=True)

        elif command == "quit":
            break
def benchmark():
    engine = TinyBeast(depth=3)

    positions = [
        chess.STARTING_FEN,
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        "r3k2r/ppp2ppp/2n1bn2/3qp3/3P4/2N1PN2/PPP2PPP/R2QKB1R w KQkq - 0 1"
    ]

    print("TINY BEAST 4K BENCHMARK")
    print("-----------------------")

    total_nodes = 0
    total_time = 0

    for index, fen in enumerate(positions, 1):
        engine.board.set_fen(fen)

        start = time.perf_counter()
        move = engine.choose_move()
        elapsed = time.perf_counter() - start

        nodes = engine.nodes
        speed = nodes / elapsed if elapsed > 0 else 0

        total_nodes += nodes
        total_time += elapsed

        print(f"\nPosition: {index}")
        print("Best move:", move)
        print("Nodes:", nodes)
        print("Time:", round(elapsed, 3), "seconds")
        print("Nodes/sec:", int(speed))

    print("\n-----------------------")
    print("TOTAL NODES:", total_nodes)
    print("TOTAL TIME:", round(total_time, 3), "seconds")
    print("AVERAGE NODES/sec:", int(
        total_nodes / total_time if total_time > 0 else 0
    ))

if __name__ == "__main__":
    if "--uci" in sys.argv:
        uci()
    elif "--benchmark" in sys.argv:
        benchmark()
    else:
        engine = TinyBeast(depth=3)
        move = engine.choose_move()

        print("Tiny Beast:", move)
        print("Nodes:", engine.nodes)