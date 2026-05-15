
SEARCH_OUTPUT_TEMPLATE = {
    "algorithm_used": "",
    "path": [],
    "cost": 0,
    "steps": 0
}

UNWEIGHTED_GRAPH = {
    "Main_Gate":       ["Parking", "Admin_Block", "Bus_Stop", "Hostel"],
    "Parking":         ["Main_Gate", "Admin_Block", "Student_Services", "Medical_Center"],
    "Admin_Block":     ["Main_Gate", "Parking", "Student_Services"],
    "Student_Services":["Admin_Block", "Parking", "Exam_Hall", "Library"],
    "Exam_Hall":       ["Student_Services", "Seminar_Room", "Science_Block"],
    "Seminar_Room":    ["Exam_Hall", "AI_Lab"],
    "Library":         ["Student_Services", "Science_Block", "AI_Lab", "Seminar_Room"],
    "AI_Lab":          ["Science_Block", "Library", "Seminar_Room"],
    "Science_Block":   ["AI_Lab", "Library", "Cafeteria", "Exam_Hall"],
    "Cafeteria":       ["Science_Block", "Medical_Center", "Hostel"],
    "Medical_Center":  ["Parking", "Cafeteria", "Bus_Stop"],
    "Bus_Stop":        ["Main_Gate", "Medical_Center", "Hostel"],
    "Hostel":          ["Main_Gate", "Bus_Stop", "Cafeteria"]
}

WEIGHTED_GRAPH = {
    "Main_Gate":       [("Parking", 2), ("Admin_Block", 4), ("Bus_Stop", 1), ("Hostel", 2)],
    "Parking":         [("Main_Gate", 2), ("Admin_Block", 2), ("Student_Services", 2), ("Medical_Center", 2)],
    "Admin_Block":     [("Main_Gate", 4), ("Parking", 2), ("Student_Services", 1)],
    "Student_Services":[("Admin_Block", 1), ("Parking", 2), ("Exam_Hall", 2), ("Library", 2)],
    "Exam_Hall":       [("Student_Services", 2), ("Seminar_Room", 1), ("Science_Block", 3)],
    "Seminar_Room":    [("Exam_Hall", 1), ("AI_Lab", 2)],
    "Library":         [("Student_Services", 2), ("Science_Block", 3), ("AI_Lab", 1), ("Seminar_Room", 2)],
    "AI_Lab":          [("Science_Block", 1), ("Library", 1), ("Seminar_Room", 2)],
    "Science_Block":   [("AI_Lab", 1), ("Library", 3), ("Cafeteria", 3), ("Exam_Hall", 3)],
    "Cafeteria":       [("Science_Block", 3), ("Medical_Center", 2), ("Hostel", 2)],
    "Medical_Center":  [("Parking", 2), ("Cafeteria", 2), ("Bus_Stop", 1)],
    "Bus_Stop":        [("Main_Gate", 1), ("Medical_Center", 1), ("Hostel", 2)],
    "Hostel":          [("Main_Gate", 2), ("Bus_Stop", 2), ("Cafeteria", 2)]
}

HEURISTIC = {
    "Main_Gate": 6.0, "Parking": 5.0, "Admin_Block": 5.5,
    "Student_Services": 4.0, "Exam_Hall": 3.5, "Seminar_Room": 2.5,
    "Library": 1.5, "AI_Lab": 0.0, "Science_Block": 1.0,
    "Cafeteria": 2.5, "Medical_Center": 4.0, "Bus_Stop": 5.5, "Hostel": 4.0
}

def _build_path(parent, start, goal):
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    path.reverse()
    return path if path[0] == start else []

def bfs(graph, start, goal):
    if start == goal:
        return [start], 0
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        node = path[-1]
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                new_path = path + [neighbor]
                if neighbor == goal:
                    return new_path, len(new_path) - 1
                visited.add(neighbor)
                queue.append(new_path)
    return [], float('inf')

def dfs(graph, start, goal):
    stack = [[start]]
    visited = {start}
    while stack:
        path = stack.pop()
        node = path[-1]
        if node == goal:
            return path, len(path) - 1
        for neighbor in reversed(graph.get(node, [])):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(path + [neighbor])
    return [], float('inf')

def dls(graph, start, goal, limit):
    def _dls_recursive(path, node, depth):
        if node == goal:
            return path
        if depth == 0:
            return None
        for neighbor in graph.get(node, []):
            if neighbor not in path:
                result = _dls_recursive(path + [neighbor], neighbor, depth - 1)
                if result is not None:
                    return result
        return None
    path = _dls_recursive([start], start, limit)
    if path:
        return path, len(path) - 1
    return [], float('inf')

def ids(graph, start, goal, max_depth=20):
    for depth in range(max_depth + 1):
        path, cost = dls(graph, start, goal, depth)
        if path:
            return path, cost
    return [], float('inf')

def ucs(graph, start, goal):
    pq = [(0, start, [start])]
    visited = {}
    while pq:
        cost, node, path = heapq.heappop(pq)
        if node in visited:
            continue
        visited[node] = cost
        if node == goal:
            return path, cost
        for neighbor, edge_cost in graph.get(node, []):
            if neighbor not in visited:
                heapq.heappush(pq, (cost + edge_cost, neighbor, path + [neighbor]))
    return [], float('inf')

def bidirectional_bfs(graph, start, goal):
    if start == goal:
        return [start], 0
    front_visited = {start: [start]}
    back_visited = {goal: [goal]}
    front_queue = deque([start])
    back_queue = deque([goal])
    def expand(queue, visited, other_visited):
        node = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited[neighbor] = visited[node] + [neighbor]
                queue.append(neighbor)
                if neighbor in other_visited:
                    return neighbor
        return None
    while front_queue or back_queue:
        if front_queue:
            meet = expand(front_queue, front_visited, back_visited)
            if meet:
                path = front_visited[meet] + list(reversed(back_visited[meet][:-1]))
                return path, len(path) - 1
        if back_queue:
            meet = expand(back_queue, back_visited, front_visited)
            if meet:
                path = front_visited[meet] + list(reversed(back_visited[meet][:-1]))
                return path, len(path) - 1
    return [], float('inf')

def greedy_bfs(graph, start, goal, heuristic=None):
    h = heuristic or HEURISTIC
    pq = [(h.get(start, 0), start, [start], 0)]
    visited = set()
    while pq:
        _, node, path, cost = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)
        if node == goal:
            return path, cost
        for neighbor, edge_cost in graph.get(node, []):
            if neighbor not in visited:
                heapq.heappush(pq, (h.get(neighbor, float('inf')), neighbor, path + [neighbor], cost + edge_cost))
    return [], float('inf')

def astar(graph, start, goal, heuristic=None):
    h = heuristic or HEURISTIC
    pq = [(h.get(start, 0), 0, start, [start])]
    visited = {}
    while pq:
        f, g, node, path = heapq.heappop(pq)
        if node in visited:
            continue
        visited[node] = g
        if node == goal:
            return path, g
        for neighbor, edge_cost in graph.get(node, []):
            if neighbor not in visited:
                new_g = g + edge_cost
                new_f = new_g + h.get(neighbor, float('inf'))
                heapq.heappush(pq, (new_f, new_g, neighbor, path + [neighbor]))
    return [], float('inf')

def rbfs(graph, start, goal, heuristic=None):
    h = heuristic or HEURISTIC
    INF = float('inf')
    def _rbfs(node, path, g, f_limit):
        if node == goal:
            return path, g, g
        successors = []
        for neighbor, cost in graph.get(node, []):
            if neighbor not in path:
                new_g = g + cost
                f = max(new_g + h.get(neighbor, INF), g + h.get(node, INF))
                successors.append((f, neighbor, new_g))
        if not successors:
            return [], INF, INF
        successors.sort(key=lambda x: x[0])
        while True:
            best_f, best_node, best_g = successors[0]
            if best_f > f_limit:
                return [], best_f, best_f
            alt = successors[1][0] if len(successors) > 1 else INF
            result, new_f, _ = _rbfs(best_node, path + [best_node], best_g, min(f_limit, alt))
            successors[0] = (new_f, best_node, best_g)
            successors.sort(key=lambda x: x[0])
            if result:
                return result, best_g, new_f
    result, cost, _ = _rbfs(start, [start], 0, float('inf'))
    return result, cost

def find_route(source, destination, graph_type="weighted", algorithm=None):
    if source not in VALID_CAMPUS_NODES:
        return {**SEARCH_OUTPUT_TEMPLATE, "algorithm_used": "none", "path": [], "cost": -1, "steps": -1}
    if destination not in VALID_CAMPUS_NODES:
        return {**SEARCH_OUTPUT_TEMPLATE, "algorithm_used": "none", "path": [], "cost": -1, "steps": -1}
    if algorithm is None:
        if graph_type == "unweighted":
            algorithm = "BFS"
        elif destination in HEURISTIC:
            algorithm = "A*"
        else:
            algorithm = "UCS"
    algo_upper = algorithm.upper()
    if algo_upper == "BFS":
        path, cost = bfs(UNWEIGHTED_GRAPH, source, destination)
    elif algo_upper == "DFS":
        path, cost = dfs(UNWEIGHTED_GRAPH, source, destination)
    elif algo_upper == "DLS":
        path, cost = dls(UNWEIGHTED_GRAPH, source, destination, limit=10)
    elif algo_upper == "IDS":
        path, cost = ids(UNWEIGHTED_GRAPH, source, destination)
    elif algo_upper == "UCS":
        path, cost = ucs(WEIGHTED_GRAPH, source, destination)
    elif algo_upper in {"BIDIRECTIONAL", "BIDIR", "BIDIRECTIONAL_BFS"}:
        path, cost = bidirectional_bfs(UNWEIGHTED_GRAPH, source, destination)
    elif algo_upper in {"GREEDY", "GREEDY_BFS"}:
        path, cost = greedy_bfs(WEIGHTED_GRAPH, source, destination)
    elif algo_upper == "A*":
        path, cost = astar(WEIGHTED_GRAPH, source, destination)
    elif algo_upper == "RBFS":
        path, cost = rbfs(WEIGHTED_GRAPH, source, destination)
    else:
        return {**SEARCH_OUTPUT_TEMPLATE, "algorithm_used": algorithm, "path": [], "cost": -1, "steps": -1}
    return {
        "algorithm_used": algorithm,
        "path": path,
        "cost": cost if cost != float('inf') else -1,
        "steps": len(path) - 1 if path else 0
    }
