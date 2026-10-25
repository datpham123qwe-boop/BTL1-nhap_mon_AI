from game_tent import logic


def dfs_search(state: logic.TentsAndTreeState, tree_index=0, on_step=None, stats=None):
    if stats is None:
        stats = {"nodes": 0}

    stats["nodes"] += 1
    if on_step is not None:
        on_step(state.grid, stats["nodes"])

    if tree_index == len(state.trees):
        return (
            state.row_tents == state.row_limits
            and state.col_tents == state.col_limits
        )

    for r, c in state.get_successors(tree_index):
        state.grid[r][c] = logic.TENT
        state.row_tents[r] += 1
        state.col_tents[c] += 1

        if dfs_search(state, tree_index + 1, on_step, stats):
            return True

        state.grid[r][c] = logic.EMPTY
        state.row_tents[r] -= 1
        state.col_tents[c] -= 1

        if on_step is not None:
            on_step(state.grid, stats["nodes"])

    return False