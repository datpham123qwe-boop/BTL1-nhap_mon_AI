import random


def make_cases():
    cases = []

    for n in (5, 7, 9):
        for seed in (11, 29, 47):
            rng = random.Random(seed + n * 100)

            # Akari: dựng cấu hình đèn hợp lệ rồi suy ra tường số.
            grid = [
                [-1 if rng.random() < .28 else -2 for _ in range(n)]
                for _ in range(n)
            ]
            bulbs, lit = set(), set()
            cells = [
                (r, c)
                for r in range(n)
                for c in range(n)
                if grid[r][c] == -2
            ]
            rng.shuffle(cells)

            for r, c in cells:
                if (r, c) in lit:
                    continue

                bulbs.add((r, c))
                lit.add((r, c))

                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = r + dr, c + dc
                    while (
                        0 <= a < n
                        and 0 <= b < n
                        and grid[a][b] == -2
                    ):
                        lit.add((a, b))
                        a, b = a + dr, b + dc

            for r in range(n):
                for c in range(n):
                    if grid[r][c] == -1 and rng.random() < .75:
                        grid[r][c] = sum(
                            (r + dr, c + dc) in bulbs
                            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        )

            cases.append(dict(
                id=f"A{n}-{seed}",
                game="akari",
                grid=grid,
                expected=True,
            ))

            # Tents: dựng các cặp cây-lều rồi chỉ giữ cây và chỉ tiêu.
            trees, tents = [], []
            cells = [(r, c) for r in range(n) for c in range(n)]
            rng.shuffle(cells)

            for r, c in cells:
                if len(trees) >= n * n // 5:
                    break

                if (r, c) in trees or any(
                    max(abs(r - a), abs(c - b)) <= 1
                    for a, b in tents
                ):
                    continue

                near = [
                    (r + dr, c + dc)
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                ]
                rng.shuffle(near)

                for a, b in near:
                    if (
                        0 <= a < n
                        and 0 <= b < n
                        and (a, b) not in trees
                        and (a, b) not in tents
                    ):
                        trees.append((a, b))
                        tents.append((r, c))
                        break

            grid = [[0] * n for _ in range(n)]
            for r, c in trees:
                grid[r][c] = 1

            cases.append(dict(
                id=f"T{n}-{seed}",
                game="tents",
                grid=grid,
                trees=trees,
                row_limits=[
                    sum(r == i for r, c in tents) for i in range(n)
                ],
                col_limits=[
                    sum(c == i for r, c in tents) for i in range(n)
                ],
                expected=True,
            ))

    cases += [
        dict(
            id="A-unsat",
            game="akari",
            grid=[[0, -2]],
            expected=False,
        ),
        dict(
            id="T-unsat",
            game="tents",
            grid=[[1, 0], [0, 0]],
            trees=[(0, 0)],
            row_limits=[0, 1],
            col_limits=[0, 1],
            expected=False,
        ),
    ]
    return cases