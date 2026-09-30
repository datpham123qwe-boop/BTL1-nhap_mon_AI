from game_minesweeper.logic import TentsAndTreeState, TENT, EMPTY


def dfs_search(state, tree_index=0):
    if tree_index == len(state.trees):
        return True

    valid_moves = state.get_successors(tree_index)
    for r, c in valid_moves:
        state.grid[r][c] = TENT
        state.row_tents[r] += 1
        state.col_tents[c] += 1

        if dfs_search(state, tree_index + 1):
            return True

        state.grid[r][c] = EMPTY
        state.row_tents[r] -= 1
        state.col_tents[c] -= 1

    return False