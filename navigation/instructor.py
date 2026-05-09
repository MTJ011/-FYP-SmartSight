# ===================== instructor.py =====================
# Produces RELATIVE navigation instructions: MOVE N, TURN LEFT/RIGHT

import heapq

# -------------------- CONFIG --------------------
# Grid size
GRID_ROWS = 14
GRID_COLS = 18

# User always starts at (0,0) for demo
START = (0, 0)

# Table (aisle) defaults: each table covers HxW cells. You can change these
# for the demo to match real measured tape sizes.
TABLE_SIZE = (3, 3)  # rows, cols

# Average human step length in feet (typical adult step ~2.5 ft)
AVG_STEP_FT = 2.5

# How many average steps make one cell. For demo the user wanted "one cell
# equals 2 human steps"; set CELL_STEP_MULT = 2 to match that, or adjust.
CELL_STEP_MULT = 2.0

# Derived value: cell size in feet
CELL_FT = AVG_STEP_FT * CELL_STEP_MULT

# Tables placement: define a "start cell" and a size (rows,cols). The code
# will expand that to the full coverage area of each table.
TABLES = {
    # scattered positions for demo (well separated)
    "food": {"start": (2, 2), "size": TABLE_SIZE},
    "drinks": {"start": (10, 3), "size": TABLE_SIZE},
    "chemicals": {"start": (4, 13), "size": TABLE_SIZE},
}

# Obstacles (rectangular areas) that block movement. Each entry is a dict
# with `start` and `size` (rows,cols). You can change these for demo.
OBSTACLES = [
    # Two-part horizontal shelf with a single gap around col 6
    {"start": (5, 1), "size": (1, 5)},
    {"start": (5, 7), "size": (1, 10)},
    # Vertical wall with a gap at row 6
    {"start": (2, 8), "size": (4, 1)},
    {"start": (7, 8), "size": (4, 1)},
    # L-shaped obstacles forcing detours
    {"start": (8, 10), "size": (3, 1)},
    {"start": (10, 10), "size": (1, 4)},
    # A block near the start to make the initial approach challenging
    {"start": (1, 5), "size": (3, 1)},
    # A couple of scattered small obstacles
    {"start": (11, 14), "size": (2, 2)},
    {"start": (3, 11), "size": (2, 1)},
]

def make_empty_grid(rows=GRID_ROWS, cols=GRID_COLS):
    return [[0 for _ in range(cols)] for _ in range(rows)]

def place_tables_on_grid(grid, tables=TABLES):
    # mark table covered cells as obstacles (1)
    for name, info in tables.items():
        r0, c0 = info["start"]
        h, w = info.get("size", TABLE_SIZE)
        cells = []
        for dr in range(h):
            for dc in range(w):
                r, c = r0 + dr, c0 + dc
                if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                    grid[r][c] = 1
                    cells.append((r, c))
        info["cells"] = cells

def place_obstacles_on_grid(grid, obstacles=OBSTACLES):
    for obs in obstacles:
        r0, c0 = obs["start"]
        h, w = obs.get("size", (1,1))
        for dr in range(h):
            for dc in range(w):
                r, c = r0 + dr, c0 + dc
                if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                    grid[r][c] = 1

# Create working grid and place tables
store_map = make_empty_grid()
place_tables_on_grid(store_map)
place_obstacles_on_grid(store_map)

start = START

HEADINGS = ["RIGHT", "DOWN", "LEFT", "UP"]
DIR_TO_HEADING = {
    (0, 1): "RIGHT",
    (1, 0): "DOWN",
    (0, -1): "LEFT",
    (-1, 0): "UP"
}

def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def astar(grid, start, goal):
    neighbors = [(0,1),(1,0),(0,-1),(-1,0)]
    open_set = [(0, start)]
    came = {}
    g = {start:0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came:
                path.append(current)
                current = came[current]
            return path[::-1]

        for dx, dy in neighbors:
            n = (current[0]+dx, current[1]+dy)
            if not (0 <= n[0] < len(grid) and 0 <= n[1] < len(grid[0])):
                continue
            if grid[n[0]][n[1]] == 1:
                continue
            ng = g[current] + 1
            if ng < g.get(n, 1e9):
                g[n] = ng
                came[n] = current
                heapq.heappush(open_set, (ng + heuristic(n, goal), n))
    return []

def compress_path(path, start_pos):
    steps = []    
    if not path:
        return steps
    prev = start_pos
    count = 0
    last_dir = None

    for p in path:
        dx, dy = p[0]-prev[0], p[1]-prev[1]
        cur_dir = DIR_TO_HEADING[(dx,dy)]
        if cur_dir == last_dir or last_dir is None:
            count += 1
        else:
            steps.append((last_dir, count))
            count = 1
        last_dir = cur_dir
        prev = p

    steps.append((last_dir, count))
    return steps


def find_nearest_approach_cell(table_name, grid, start):
    """Return (best_cell, path) where best_cell is a free cell adjacent to
    the table that has the shortest path from start. Returns (None, []) if
    none found."""
    info = TABLES.get(table_name)
    if not info:         
        return None, []

    # map candidate approach cell -> set of adjacent table cells
    candidates = {}
    for (r, c) in info.get("cells", []):
        for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]):
                if grid[nr][nc] == 0:
                    candidates.setdefault((nr, nc), set()).add((r, c))

    best = None
    best_path = []
    best_len = 1e9
    best_adj_table_cell = None
    for cand, adj_cells in candidates.items():
        path = astar(grid, start, cand)
        if path and len(path) < best_len:
            # pick the adjacent table cell that's nearest to candidate
            best_adj = min(adj_cells, key=lambda t: heuristic(cand, t))
            best = cand
            best_path = path
            best_len = len(path)
            best_adj_table_cell = best_adj

    return best, best_path, best_adj_table_cell


def compute_distance_and_steps(path_len_cells):
    """Given path length in cells (number of moves), compute distance in
    feet and number of human steps (rounded up)."""
    feet = path_len_cells * CELL_FT
    steps = int((feet / AVG_STEP_FT) + 0.9999)
    meters = feet * 0.3048
    return feet, meters, steps


def generate_instructions_steps(destination=None, initial_heading="RIGHT"):
    """Produce final instructions where MOVE counts are expressed in
    human steps (integers). This was the compatibility helper previously
    added. Use `generate_instructions` (cell-based) for the original
    behaviour."""
    # reuse previous implementation by converting cell-based segments
    # to human steps
    if destination is None:
        print("Where would you like to go? Options:")
        for k in TABLES.keys():
            print(" -", k)
        destination = input("Enter destination (food/drinks/chemicals): ").strip().lower()

    if destination not in TABLES:
        raise ValueError("Unknown destination")

    approach_cell, path, adj_table_cell = find_nearest_approach_cell(destination, store_map, START)
    if not path:
        raise RuntimeError("No path to destination found")

    compressed = compress_path(path, START)

    # compute total and per-segment steps
    total_cells = sum(c for _, c in compressed)
    total_feet = total_cells * CELL_FT
    total_steps = int((total_feet / AVG_STEP_FT) + 0.9999)

    per_segment_steps = []
    acc = 0
    for heading, cells in compressed:
        seg_feet = cells * CELL_FT
        seg_steps = int((seg_feet / AVG_STEP_FT) + 0.5)
        per_segment_steps.append((heading, seg_steps))
        acc += seg_steps

    if acc != total_steps and per_segment_steps:
        per_segment_steps[-1] = (per_segment_steps[-1][0], per_segment_steps[-1][1] + (total_steps - acc))

    # build final instructions
    instructions = []
    current_heading = initial_heading
    for heading, steps in per_segment_steps:
        idx_now = HEADINGS.index(current_heading)
        idx_target = HEADINGS.index(heading)
        diff = (idx_target - idx_now) % 4
        if diff == 1:
            instructions.append(("TURN", "RIGHT"))
        elif diff == 3:
            instructions.append(("TURN", "LEFT"))
        elif diff == 2:
            instructions.append(("TURN", "RIGHT"))
            instructions.append(("TURN", "RIGHT"))

        instructions.append(("MOVE", steps))
        current_heading = heading

    # final facing
    if adj_table_cell:
        dest = path[-1]
        vr = adj_table_cell[0] - dest[0]
        vc = adj_table_cell[1] - dest[1]
        if (vr, vc) in DIR_TO_HEADING:
            desired_heading = DIR_TO_HEADING[(vr, vc)]
            idx_now = HEADINGS.index(current_heading)
            idx_target = HEADINGS.index(desired_heading)
            diff = (idx_target - idx_now) % 4
            if diff == 1:
                instructions.append(("TURN", "RIGHT"))
            elif diff == 3:
                instructions.append(("TURN", "LEFT"))
            elif diff == 2:
                instructions.append(("TURN", "RIGHT"))
                instructions.append(("TURN", "RIGHT"))

    instructions.append(("END", None))
    return instructions


def generate_instructions(destination=None, initial_heading="RIGHT"):
    """Original behaviour: return TURN/MOVE instructions where MOVE counts
    are number of grid cells (not converted to human steps). If
    `destination` is None the function prompts the user to choose one."""
    if destination is None:
        print("Where would you like to go? Options:")
        for k in TABLES.keys():
            print(" -", k)
        destination = input("Enter destination (food/drinks/chemicals): ").strip().lower()

    if destination not in TABLES:
        raise ValueError("Unknown destination")

    approach_cell, path, adj_table_cell = find_nearest_approach_cell(destination, store_map, START)
    if not path:
        raise RuntimeError("No path to destination found")

    # re-use the lower-level path-to-instruction generator (cells)
    instrs = generate_instructions_for_path(START, path, initial_heading=initial_heading, final_face_target=adj_table_cell)
    return instrs

def generate_instructions_for_path(start_pos, path, initial_heading="RIGHT", final_face_target=None):
    compressed = compress_path(path, start_pos)
    instructions = []

    current_heading = initial_heading

    for heading, count in compressed:
        idx_now = HEADINGS.index(current_heading)
        idx_target = HEADINGS.index(heading)
        diff = (idx_target - idx_now) % 4

        if diff == 1:
            instructions.append(("TURN", "RIGHT"))
        elif diff == 3:
            instructions.append(("TURN", "LEFT"))
        elif diff == 2:
            instructions.append(("TURN", "RIGHT"))
            instructions.append(("TURN", "RIGHT"))

        instructions.append(("MOVE", count))
        current_heading = heading

    # If requested, ensure the user faces the table on arrival
    if final_face_target and path:
        dest = path[-1]
        # verify final_face_target is adjacent to dest
        vr = final_face_target[0] - dest[0]
        vc = final_face_target[1] - dest[1]
        if (vr, vc) in DIR_TO_HEADING:
            desired_heading = DIR_TO_HEADING[(vr, vc)]
            idx_now = HEADINGS.index(current_heading)
            idx_target = HEADINGS.index(desired_heading)
            diff = (idx_target - idx_now) % 4
            if diff == 1:
                instructions.append(("TURN", "RIGHT"))
            elif diff == 3:
                instructions.append(("TURN", "LEFT"))
            elif diff == 2:
                instructions.append(("TURN", "RIGHT"))
                instructions.append(("TURN", "RIGHT"))

    instructions.append(("END", None))
    return instructions

def print_grid(grid, tables, start):
    rows = len(grid)
    cols = len(grid[0])
    out = []
    # build a display map
    disp = [["." for _ in range(cols)] for _ in range(rows)]
    # mark obstacles
    for obs in OBSTACLES:
        r0, c0 = obs["start"]
        h, w = obs.get("size", (1,1))
        for dr in range(h):
            for dc in range(w):
                r, c = r0 + dr, c0 + dc
                if 0 <= r < rows and 0 <= c < cols:
                    disp[r][c] = "X"
    for name, info in tables.items():
        label = name[0].upper()
        for r, c in info.get("cells", []):
            disp[r][c] = label
    sr, sc = start
    disp[sr][sc] = "S"
    print("Grid (S=start, F=food, D=drinks, C=chemicals, X=obstacle):")
    for r in range(rows):
        print(" ".join(disp[r]))


if __name__ == "__main__":
    print_grid(store_map, TABLES, START)
    print(f"Cell size: {CELL_FT:.2f} ft ({CELL_FT*0.3048:.2f} m). Avg step {AVG_STEP_FT:.2f} ft.")
    print("Where would you like to go? Options:")
    for k in TABLES.keys():
        print(" -", k)

    choice = input("Enter destination (food/drinks/chemicals): ").strip().lower()
    if choice not in TABLES:
        print("Unknown destination. Exiting.")
    else:
        info = TABLES[choice]
        print(f"Table '{choice}' start cell: {info['start']}, size: {info.get('size', TABLE_SIZE)}")
        dest_cell, path, adj_table_cell = find_nearest_approach_cell(choice, store_map, START)
        if not path:
            print("No path to destination found.")
        else:
            feet, meters, steps = compute_distance_and_steps(len(path))
            print(f"Approach cell: {dest_cell}; path length {len(path)} cells")
            if adj_table_cell:
                print(f"Adjacent table cell (to face): {adj_table_cell}")
            print(f"Distance: {feet:.2f} ft ({meters:.2f} m) -> approx {steps} steps")
            # allow user to optionally specify initial facing direction
            ih = input("Initial facing (RIGHT/DOWN/LEFT/UP) [default RIGHT]: ").strip().upper()
            if ih not in HEADINGS:
                ih = "RIGHT"
            instr = generate_instructions_for_path(START, path, initial_heading=ih, final_face_target=adj_table_cell)
            print("Instructions:")
            for i in instr:
                print(i)


