import copy

EMPTY , TREE , TENT, GRASS = 0,1,2,3

class TentsAndTreeState:
    def __init__(self,grid,row_limits,col_limits,trees):
        self.grid=grid
        self.row_limits=row_limits
        self.col_limits=col_limits
        self.trees=trees

        #đếm số lều đã đặt trên mỗi hàng cột để kiểm tra ràng buộc
        row_tents=[]
        for row in grid:
            num_tent=0
            for cell in row:
                if cell==TENT:
                   num_tent=num_tent+1
            row_tents.append(num_tent) 
        self.row_tents=row_tents

        col_tents=[]
        for c in range(len(grid[0])):
            num_tent=0
            for r in range(len(grid)):
                if grid[r][c]==TENT:
                    num_tent=num_tent+1
            col_tents.append(num_tent)
        self.col_tents=col_tents

    def is_valid_tent_placement(self,r,c):
        """kiem tra xem co the dat leu tai o (r,c) hay khong"""
        if not (0<=r<len(self.grid) and 0<=c<len(self.grid[0])): return False
        if self.grid[r][c]!=EMPTY: return False


        if self.row_tents[r]>=self.row_limits[r]: return False
        if self.col_tents[c]>=self.col_limits[c]: return False

        directions=[(1,0),(0,1),(-1,0),(0,-1),(1,1),(-1,-1),(-1,1),(1,-1)]
        for dr,dc in directions:
            nr,nc=dr+r,dc+c
            if 0<=nr<len(self.grid) and 0<=nc<len(self.grid[0]):
                if self.grid[nr][nc]==TENT:
                    return False

        return True

    def get_successors(self,tree_index):
        """ham sinh cac trang thai ke tiep"""
        if tree_index>=len(self.trees):
            return []
        successors=[]
        tree_r,tree_c=self.trees[tree_index]
        adjcent_positions=[(tree_r-1,tree_c),(tree_r+1,tree_c),(tree_r,tree_c-1),(tree_r,tree_c+1)]
        for r,c in adjcent_positions:
            if self.is_valid_tent_placement(r,c):
                successors.append((r, c))
        return successors
            