from game_akari.logic import AkariProblem
from game_akari.blind_search import solve_dfs
from game_akari.heuristic_search import solve_astar

from game_tent.logic import TentsAndTreeState
from game_tent.blind_search import dfs_search
from game_tent.heuristic_search import A_star_search


def prepare(case):
    if case["game"] == "akari":
        return AkariProblem(case["grid"])

    return TentsAndTreeState(
        [r[:] for r in case["grid"]],
        case["row_limits"][:],
        case["col_limits"][:],
        [tuple(t) for t in case["trees"]],
    )


def solve(case, state, algorithm, on_step=None):
    if case["game"] == "akari":
        fn = solve_dfs if algorithm == "DFS" else solve_astar
        return fn(state, on_step=on_step)

    if algorithm == "DFS":
        stats = {"nodes": 0}
        ok = dfs_search(state, on_step=on_step, stats=stats)
        return (state if ok else None), stats["nodes"]

    return A_star_search(state, on_step=on_step)


def valid(case, solution):
    if solution is None:
        return False

    if case["game"] == "akari":
        return AkariProblem(case["grid"]).is_goal(solution)

    grid = solution.grid
    tents = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }
    trees = [tuple(t) for t in case["trees"]]

    if len(tents) != len(trees):
        return False
    if any(grid[r][c] != 1 for r, c in trees):
        return False

    if [
        sum(r == i for r, c in tents)
        for i in range(len(grid))
    ] != case["row_limits"]:
        return False

    if [
        sum(c == i for r, c in tents)
        for i in range(len(grid[0]))
    ] != case["col_limits"]:
        return False

    if any(
        a != b and max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1
        for a in tents
        for b in tents
    ):
        return False

    # Kiểm tra tồn tại ghép cặp 1-1 giữa toàn bộ cây và lều.
    matched = {}

    def augment(i, seen):
        r, c = trees[i]
        for tent in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if tent not in tents or tent in seen:
                continue
            seen.add(tent)
            if tent not in matched or augment(matched[tent], seen):
                matched[tent] = i
                return True
        return False

    return all(augment(i, set()) for i in range(len(trees)))