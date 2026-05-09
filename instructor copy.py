# ===================== instructor.py =====================
# Produces RELATIVE navigation instructions: MOVE N, TURN LEFT/RIGHT

import heapq

store_map = [
    [0,0,0,1,0],
    [0,1,0,1,0],
    [0,1,0,0,0],
    [0,0,0,1,0],
    [0,0,0,0,0]
]

start = (0, 0)
goal = (4, 4)

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

def compress_path(path):
    steps = []
    if not path:
        return steps
    prev = start
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

def generate_instructions():
    path = astar(store_map, start, goal)
    compressed = compress_path(path)
    instructions = []

    current_heading = "RIGHT"

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

    instructions.append(("END", None))
    return instructions

if __name__ == "__main__":
    for i in generate_instructions():
        print(i)

