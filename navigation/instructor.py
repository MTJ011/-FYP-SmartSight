# ===================== instructor.py =====================
# SmartSight Navigation System
# Stage 1: Unlabelled real-store occupancy map
# 0 = walkable
# 1 = blocked shelf / wall / obstacle

import heapq
import math
import numpy as np
import matplotlib.pyplot as plt

CELL_SIZE_IN = 6
STEP_LENGTH_IN = 24

STORE_WIDTH_IN = 300
STORE_HEIGHT_IN = 300

GRID_ROWS = STORE_HEIGHT_IN // CELL_SIZE_IN
GRID_COLS = STORE_WIDTH_IN // CELL_SIZE_IN

START = (GRID_ROWS - 1, GRID_COLS // 2)
DEFAULT_INITIAL_HEADING = "UP"

HEADINGS = ["RIGHT", "DOWN", "LEFT", "UP"]

DIR_TO_HEADING = {
    (0, 1): "RIGHT",
    (1, 0): "DOWN",
    (0, -1): "LEFT",
    (-1, 0): "UP",
}

# Format: (row, col, height, width)
STRUCTURE_RECTS = [
    # TOP
    (0, 2, 3, 39),
    (0, 42, 17, 8),

    # LEFT SIDE
    (0, 0, 25, 2),
    (18, 0, 8, 5),
    (27, 0, 22, 12),

    # RIGHT SIDE
    (17, 40, 8, 10),
    (24, 45, 16, 5),
    (40, 29, 9, 21),

    # TOP INNER ISLANDS
    (6, 11, 15, 8),
    (21, 11, 4, 10),
    (6, 27, 15, 8),
    (21, 27, 4, 10),

    # LOWER INNER ISLANDS
    (26, 19, 13, 6),
    (26, 30, 13, 6),
]


def make_empty_grid():
    return [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]


def apply_rect(grid, rect):
    r0, c0, h, w = rect

    for r in range(r0, r0 + h):
        for c in range(c0, c0 + w):
            if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                grid[r][c] = 1


def build_store_map():
    grid = make_empty_grid()

    for rect in STRUCTURE_RECTS:
        apply_rect(grid, rect)

    # Gate opening at bottom center
    for r in range(GRID_ROWS - 2, GRID_ROWS):
        for c in range(18, 32):
            grid[r][c] = 0

    grid[START[0]][START[1]] = 0
    return grid


store_map = build_store_map()


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):
    neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    open_set = [(0, start)]
    came = {}
    g = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came:
                path.append(current)
                current = came[current]
            return path[::-1]

        for dr, dc in neighbors:
            nr = current[0] + dr
            nc = current[1] + dc
            nxt = (nr, nc)

            if not (0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS):
                continue

            if grid[nr][nc] == 1:
                continue

            new_g = g[current] + 1

            if new_g < g.get(nxt, 1e9):
                g[nxt] = new_g
                came[nxt] = current
                heapq.heappush(open_set, (new_g + heuristic(nxt, goal), nxt))

    return []


def compress_path(path, start_pos):
    if not path:
        return []

    steps = []
    prev = start_pos
    count = 0
    last_dir = None

    for p in path:
        dr = p[0] - prev[0]
        dc = p[1] - prev[1]
        cur_dir = DIR_TO_HEADING[(dr, dc)]

        if cur_dir == last_dir or last_dir is None:
            count += 1
        else:
            steps.append((last_dir, count))
            count = 1

        last_dir = cur_dir
        prev = p

    steps.append((last_dir, count))
    return steps


def cells_to_human_steps(cell_count):
    inches = cell_count * CELL_SIZE_IN
    return max(1, math.ceil(inches / STEP_LENGTH_IN))


def turn_instructions(current_heading, target_heading):
    instructions = []

    idx_now = HEADINGS.index(current_heading)
    idx_target = HEADINGS.index(target_heading)
    diff = (idx_target - idx_now) % 4

    if diff == 1:
        instructions.append(("TURN", "RIGHT"))
    elif diff == 3:
        instructions.append(("TURN", "LEFT"))
    elif diff == 2:
        instructions.append(("TURN", "RIGHT"))
        instructions.append(("TURN", "RIGHT"))

    return instructions


def generate_instructions_for_goal(goal):
    path = astar(store_map, START, goal)

    if not path:
        return [], []

    compressed = compress_path(path, START)

    instructions = []
    current_heading = DEFAULT_INITIAL_HEADING

    for heading, cell_count in compressed:
        instructions.extend(turn_instructions(current_heading, heading))
        instructions.append(("MOVE", cells_to_human_steps(cell_count)))
        current_heading = heading

    instructions.append(("END", None))
    return instructions, path


def print_grid(grid, start, path=None):
    display = [["." for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if grid[r][c] == 1:
                display[r][c] = "#"

    if path:
        for r, c in path:
            if display[r][c] == ".":
                display[r][c] = "*"

    sr, sc = start
    display[sr][sc] = "S"

    print()
    print(f"Grid: {GRID_ROWS} x {GRID_COLS}")
    print("S = start/gate")
    print(". = walkable")
    print("# = blocked shelf/wall/obstacle")
    print("* = path")
    print()

    for row in display:
        print(" ".join(row))


def draw_grid_map(grid, start, path=None):
    canvas = np.zeros((GRID_ROWS, GRID_COLS))

    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if grid[r][c] == 1:
                canvas[r][c] = 1

    if path:
        for r, c in path:
            if canvas[r][c] == 0:
                canvas[r][c] = 0.5

    sr, sc = start
    canvas[sr][sc] = 0.8

    plt.figure(figsize=(10, 10))
    plt.imshow(canvas, origin="upper", interpolation="nearest", aspect="equal")
    plt.title("SmartSight Store Occupancy Grid")
    plt.grid(True)
    plt.xticks(range(GRID_COLS))
    plt.yticks(range(GRID_ROWS))
    plt.savefig("store_unlabelled_grid_preview.png", dpi=200)
    plt.show()


if __name__ == "__main__":
    print_grid(store_map, START)

    print()
    print("Enter a test goal cell.")
    print("Example:")
    print("row = 24")
    print("col = 24")
    print()

    row_text = input("Goal row: ").strip()

    if row_text == "":
        draw_grid_map(store_map, START)
    else:
        col_text = input("Goal col: ").strip()
        goal = (int(row_text), int(col_text))

        if not (0 <= goal[0] < GRID_ROWS and 0 <= goal[1] < GRID_COLS):
            print("Goal outside grid.")
        elif store_map[goal[0]][goal[1]] == 1:
            print("Goal inside obstacle.")
        else:
            instructions, path = generate_instructions_for_goal(goal)

            if not path:
                print("No path found.")
            else:
                print_grid(store_map, START, path=path)
                print()
                print("Instructions:")
                for instr in instructions:
                    print(instr)

                draw_grid_map(store_map, START, path=path)