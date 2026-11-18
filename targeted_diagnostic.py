
import chess
import chess.engine
import sys

from main import TinyBeast

STOCKFISH_PATH = "/usr/games/stockfish"
TINY_DEPTH = 4
TINY_TIME = 1.5
STOCKFISH_DEPTH = 14

POSITIONS = [
    {
        "name": "Game 7 — przed 23.Nc6",
        "historical_move": "Nc6",
        "moves": """
            e4 e6 d4 d5 Nc3 Nf6 e5 Nfd7 Nf3 c5
            h4 cxd4 Qxd4 Qc7 Bf4 a6 O-O-O Bc5
            Qd2 b5 Nxd5 exd5 e6 Bd6 exd7+ Bxd7
            Bxd6 Qxd6 Qg5 O-O Rxd5 Qe6 c4 Rc8
            b3 a5 Kb1 a4 cxb5 axb3 axb3 Qb6
            Nd4 Qa5
        """,
    },
    {
        "name": "Game 10 — przed 40...Qxd8",
        "historical_move": "Qxd8",
        "moves": """
            c4 e5 Nc3 Nf6 g3 d5 cxd5 Nxd5 Nf3
            Nxc3 bxc3 Nc6 Qc2 Bc5 Bg2 O-O O-O a5
            e3 Qd6 d4 Bb6 a4 f5 Ba3 Qe6 Bxf8 Kxf8
            h4 Kg8 Ng5 Qc4 Rab1 exd4 exd4 Nxd4
            Qb2 Ne2+ Kh2 Nxc3 Rbe1 Bd7 Rc1 Nxa4
            Qb1 Nc3 Qb2 Bd4 Qxb7 Rf8 Nf3 Bf6
            Rfe1 Bb5 Ng5 c5 Ne6 Re8 Nf4 Qd4
            Rxe8+ Bxe8 Re1 Bf7 Qc8+ Qd8 Qxf5
            c4 h5 Qd2 Re3 Bd8 Qc8 Nb1 Re5 c3
            Rd5 Be8 Rxd8
        """,
    },
]


def replay_position(data):
    board = chess.Board()

    for number, san in enumerate(data["moves"].split(), start=1):
        try:
            move = board.parse_san(san)
            board.push(move)
        except Exception as error:
            raise ValueError(
                f"Nie można odtworzyć ruchu {number}: {san}\n"
                f"Pozycja: {board.fen()}\n"
                f"Błąd: {error}"
            ) from error

    return board


def score_value(info, turn):
    score = info["score"].pov(turn)
    return score.score(mate_score=100000)


def analyze_position(data, tiny, stockfish):
    print("\n" + "=" * 65, flush=True)
    print(data["name"], flush=True)
    print("=" * 65, flush=True)

    board = replay_position(data)
    legal_moves = list(board.legal_moves)

    print("FEN:", board.fen(), flush=True)
    print(
        "Na ruchu:",
        "White" if board.turn == chess.WHITE else "Black",
        flush=True,
    )
    print("Liczba legalnych ruchów:", len(legal_moves), flush=True)
    print(
        "Legalne ruchy:",
        " ".join(board.uci(move) for move in legal_moves),
        flush=True,
    )

    historical = board.parse_san(data["historical_move"])
    print(
        "Historyczny ruch:",
        data["historical_move"],
        "| UCI:",
        historical.uci(),
        flush=True,
    )

    print("\n--- Tiny Beast ---", flush=True)
    tiny_move = tiny.best_move(
        board.copy(stack=False),
        depth=TINY_DEPTH,
        movetime=TINY_TIME,
    )

    if tiny_move is None:
        print("Tiny Beast nie zwrócił ruchu.", flush=True)
    else:
        print(
            "Wybór Tiny Beast:",
            board.san(tiny_move),
            "| UCI:",
            tiny_move.uci(),
            flush=True,
        )

    print("\n--- Stockfish ---", flush=True)
    print(
        f"Analiza wszystkich legalnych ruchów, depth {STOCKFISH_DEPTH}",
        flush=True,
    )

    infos = stockfish.analyse(
        board,
        chess.engine.Limit(depth=STOCKFISH_DEPTH),
        multipv=len(legal_moves),
    )

    if isinstance(infos, dict):
        infos = [infos]

    ranking = []

    for info in infos:
        pv = info.get("pv", [])
        if not pv:
            continue

        move = pv[0]
        ranking.append({
            "move": move,
            "score": score_value(info, board.turn),
            "depth": info.get("depth", 0),
        })

    ranking.sort(key=lambda item: item["score"], reverse=True)

    print("\nTOP 5 STOCKFISHA:", flush=True)

    for number, item in enumerate(ranking[:5], start=1):
        print(
            f"{number}. {board.san(item['move'])}"
            f" | {item['move'].uci()}"
            f" | {item['score']} cp"
            f" | depth {item['depth']}",
            flush=True,
        )

    by_move = {
        item["move"]: item
        for item in ranking
    }

    print("\nPORÓWNANIE:", flush=True)

    for label, move in [
        ("Ruch historyczny", historical),
        ("Wybór Tiny Beast", tiny_move),
    ]:
        if move is None:
            continue

        result = by_move.get(move)

        if result:
            print(
                f"{label}: {board.san(move)}"
                f" | {result['score']} cp"
                f" | depth {result['depth']}",
                flush=True,
            )
        else:
            print(
                f"{label}: {board.san(move)}"
                " | brak wyniku w rankingu MultiPV",
                flush=True,
            )

    print("Koniec analizy pozycji.", flush=True)


def main():
    tiny = TinyBeast()
    stockfish = chess.engine.SimpleEngine.popen_uci(
        STOCKFISH_PATH
    )

    try:
        stockfish.configure({
            "Threads": 1,
            "Hash": 256,
        })

        for data in POSITIONS:
            try:
                analyze_position(data, tiny, stockfish)
            except Exception as error:
                print(
                    "\nBŁĄD DIAGNOSTYKI:",
                    data["name"],
                    str(error),
                    flush=True,
                )

    finally:
        stockfish.quit()

    print("\nDIAGNOSTYKA ZAKOŃCZONA.", flush=True)


if __name__ == "__main__":
    main()
