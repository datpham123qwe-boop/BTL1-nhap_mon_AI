from game_tent.logic import TentsAndTreeState, TENT, EMPTY


"""def dfs_search(state, tree_index=0):
    if tree_index == len(state.trees):
        return True

    for r, c in state.get_successors(tree_index, check_limits=False):
        state.grid[r][c] = TENT
        state.row_tents[r] += 1
        state.col_tents[c] += 1

        if dfs_search(state, tree_index + 1):
            return True

        state.grid[r][c] = EMPTY
        state.row_tents[r] -= 1
        state.col_tents[c] -= 1

    return False
    """
def dfs_search(state, tree_index=0, on_step=None, stats=None):
    if stats is None:
        stats = {"nodes": 0}
    stats["nodes"] += 1
    if on_step is not None:
        on_step(state.grid, stats["nodes"])

    if tree_index == len(state.trees):
        return (state.row_tents == state.row_limits
                and state.col_tents == state.col_limits)

    for r, c in state.get_successors(tree_index, check_limits=False):
        state.grid[r][c] = TENT
        state.row_tents[r] += 1
        state.col_tents[c] += 1
        if dfs_search(state, tree_index + 1, on_step, stats):
            return True
        state.grid[r][c] = EMPTY
        state.row_tents[r] -= 1
        state.col_tents[c] -= 1
    return False