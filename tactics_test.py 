
import chess
import chess.engine

from main import TinyBeast


MOVE_TIME = 0.75
STOCKFISH_DEPTH = 10

POSITIONS = [
    (
        "French — przed błędnym Nxd4",
        [
            "e4", "e6", "d4", "d5", "Nc3", "Nf6",
            "e5", "Nfd7", "Nf3", "Nc6", "Bd3",
            "f6", "Bf4", "g5", "Nxg5"
        ],
    ),
    (
        "French — obrona po Qh5+",
        [
            "e4", "e6", "d4", "d5", "Nc3", "Nf6",
            "e5", "Nfd7", "Nf3", "Nc6", "Bd3",
            "f6", "Bf4", "g5", "Nxg5", "Nxd4", "Qh5+"
        ],
    ),
    (
        "English — przed błędnym h6",
        [
            "c4", "e5", "Nc3", "Nf6", "g3", "d5",
            "cxd5", "Nxd5", "Nf3", "Nxc3", "bxc3",
            "Nc6", "Qa4", "Bd6", "Bg2", "O-O",
            "d3", "Bd7", "Qc2", "b6", "O-O",
            "a5", "d4", "exd4", "cxd4", "Nb4",
            "Qb1", "c5", "Ng5"
        ],
    ),
]


def build_position(moves):
    board = chess.Board()

    for san in moves:
        try:
            board.push_san(san)
        except ValueError as error:
            raise ValueError(
                f"Invalid test sequence at {san}: {error}"
            )

    return board


def immediate_mates(board):
    mates = []

    for move in list(board.legal_moves):
        board.push(move)

        if board.is_checkmate():
            mates.append(move.uci())

        board.pop()

    return mates


def test_move(board, move):
    if move is None or move not in board.legal_moves:
        return "INVALID", "INVALID"

    san = board.san(move)
    after = board.copy()
    after.push(move)

    mates = immediate_mates(after)

    return san, ", ".join(mates) if mates else "none"


def main():
    tiny = TinyBeast()

    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/usr/games/stockfish"
    )

    try:
        print("\n========== TACTICAL DIAGNOSTIC ==========\n")

        for name, moves in POSITIONS:
            board = build_position(moves)

            print("\nPOSITION:", name)
            print("FEN:", board.fen())
            print(
                "SIDE TO MOVE:",
                "White" if board.turn else "Black"
            )

            tiny_move = tiny.best_move(
                board.copy(),
                depth=4,
                movetime=MOVE_TIME
            )

            sf_info = stockfish.analyse(
                board,
                chess.engine.Limit(depth=STOCKFISH_DEPTH)
            )

            sf_move = (
                sf_info["pv"][0]
                if sf_info.get("pv")
                else None
            )

            tiny_san, tiny_danger = test_move(
                board, tiny_move
            )

            sf_san, sf_danger = test_move(
                board, sf_move
            )

            print("Tiny Beast:", tiny_san)
            print(
                "Mate in one after Tiny Beast:",
                tiny_danger
            )

            print("Stockfish:", sf_san)
            print(
                "Mate in one after Stockfish:",
                sf_danger
            )

            print(
                "Same move:",
                "YES" if tiny_move == sf_move else "NO"
            )

            print("----------------------------------------")

        print("\nDIAGNOSTIC FINISHED")

    finally:
        stockfish.quit()


if __name__ == "__main__":
    main()
