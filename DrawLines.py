import tkinter as tki
from cmath import phase
from collections import deque

# Master Tkinter Window
master = tki.Tk()

canvas = tki.Canvas(master, width=1000, height=1000, background="white")
canvas.pack()

# Defining the Outer frame points
left, top, right, bot = 250, 250, 750, 750
# Seems redundant but makes it more clear in some part of the code
frame_borders = [left, top, right, bot]

canvas.create_rectangle(left, top, right, bot)


class Line():
    """
    Line in drawing, capable of saving the line equation and containing points
    p1, p2 (tuple [2]): points on canvas, a tuple of numbers which get converted into integers
                        every time
    m (float): steepness according to the linear equation y = mx + b
    b (float): bias according to the linear equation y = mx + b
    points (list of tuples[2]): The list containing all intersection points
                                (tuples of two integer values) with other lines
    """

    def __init__(self, p1, p2):
        # Both endpoints of the line on the frame
        self.m = calc_steepness(p1, p2)
        self.b = calc_bias(p1, p2)
        self.points = [tuple([int(i) for i in p1]),
                       tuple([int(i) for i in p2])]
        # possibly change data structure into set, but sort is than not available...

    def __str__(self):
        return f"Line from {self.points[0]} to {self.points[-1]}, containing points {self.points}."

    def add_point(self, point):
        """
        Adds a point to the line if it doesn't contain it already
        """
        # Convert coordinates to integer values
        int_point = tuple([int(i) for i in point])
        if int_point not in self.points:
            self.points.append(int_point)

    def calc_intersection(self, other_line):
        """
        Calculates the intersection between two lines
        Returns false if there is no intersection, the intersection otherwise
        """
        if (self.m == other_line.m):
            return False
        intersec_x = - (self.b - other_line.b) / (self.m - other_line.m)
        intersec_y = self.m * intersec_x + self.b
        return (intersec_x, intersec_y)

    def contains_same_points(self, p1, p2):
        """
        Checks if there is already a line containing p1 and p2 and therefore is equal
        """
        for p in [p1, p2]:
            if tuple([int(i) for i in p]) not in self.points:
                return False
        return True


class Edge():
    """
    Edge object containing two points defining it and the steepness
    p1, p2 (tuple [2]): points on canvas, a tuple of numbers which get converted into integers
                        every time
    m (float): steepness according to the linear equation y = mx + b
    """

    def __init__(self, p1, p2, m):
        self.p1 = p1
        self.p2 = p2
        self.m = m

    def __str__(self):
        return f"Edge from {self.p1} to {self.p2} with steepness {self.m}"

    def contains_point(self, p):
        """
        Checks if the edge contains the given point p
        """
        if (p == self.p1 or p == self.p2):
            return True
        return False

    def get_other_point(self, p):
        """
        Returns the second point of the edge, given the first
        """
        if (p == self.p1):
            return self.p2
        # Maybe erased in the future if this is stable for faster computation
        elif (p == self.p2):
            return self.p1
        else:
            raise ValueError(f"Edge with points {self.p1} and {self.p2} does "
                             f"not contain the given point {p}.")

    def calc_vector_angle(self, p):
        """
        Returns the angle of the vector pointing from the other point of the edge to p
        with respect to the horizontal axis.
        It is negative above and positive below since the canvas coordinates rise with going down.
        """
        op = self.get_other_point(p)
        return phase((p[0] - op[0]) + (p[1] - op[1]) * 1j)

    def is_frame_edge(self):
        """
        Checks whether the edge is a frame edge or not. If it is a frame edge, it returns
        the index of the frame_borders, meaning 0, 1, 2, 3 for left, top, right, bot.
        If its not on the frame, it returns since 0 is already "False".

        """
        if self.m == float("-inf"):  # Check for vertical edges
            if self.p1[0] == left:
                return 0
            else:
                return 2
        elif self.m == 0.0:     # Check for horizontal edges
            if self.p1[1] == top:
                return 1
            else:
                return 3
        return -1

    def is_viable_direction(self, frame_border_idx, target_point, direction):
        """
        Checks if a rotating direction is viable for a edge on the frame.
        frame_border_idx: frame_border index, meaning 0, 1, 2, 3 for left, top, right, bot
        target_point is the targeted point.
        direction is 1 for clockwise, -1 for anti-clockwise

        """
        # Over complicated "simplification" for a wide if-else tree
        # Basically meaning: If its left or top and angle is positive, anticlockwise is viable and
        # vice versa for right or bot
        if (frame_border_idx < 2 and self.calc_vector_angle(target_point) <= 0):
            return (direction == 1)
        elif (frame_border_idx >= 2 and self.calc_vector_angle(target_point) > 0):
            return (direction == 1)
        return (direction == -1)

    def is_cp(self, p, direction):
        """
        Checks whether the given parameters are
        cp: clockwise direction with a positive angle or anticlockwise with negative angle
        acp: anticlockwise direction with positive angle or clockwise with negative angle
        Returns True for cp and False for acp
        """
        if (direction == 1 and self.calc_vector_angle(p) > 0) or (
                direction == -1 and self.calc_vector_angle(p) <= 0):
            return True
        return False


def point_is_within_frame(p):
    """
    Checks if the given point p is within the borders of the frame

    Args:
        p (tuple [2]): point to check

    Returns:
        in_frame (bool)

    """
    if (p[0] < left or p[0] > right or p[1] < top or p[1] > bot):
        return False
    else:
        return True


def draw_point(p, size=4, fillcolor="blue"):
    """
    Draw a point on canvas

    Args:
        p (tuple [2]): Point with x and y coordinate
        size (float, default: 4)
        fillcolor (string, default: "blue")

    """
    canvas.create_oval(p[0] - size, p[1] - size, p[0] +
                       size, p[1] + size, fill=fillcolor)


def draw_line_within_frame(p1, p2):
    """
    Draw a line on canvas from an outer point on the frame through an inner
    point within the frame to the other side of the frame.

    Args:
        p1 (tuple [2]): Point with x and y coordinate (outer point on frame)
        p2 (tuple [2]): Point with x and y coordinate (inner point within frame)
        size (float, default: 4)
        fillcolor (string, default: "blue")

    """

    target = calc_target_point_rect(p1, p2)
    canvas.create_line(p1[0], p1[1], target[0], target[1], width=4)


def calc_steepness(p1, p2):
    """
    Calculate steepness for a line between two points

    Args:
        p1 (tuple [2]): Point with x and y coordinate
        p2 (tuple [2]): Point with x and y coordinate

    Returns:
        Steepness (float)

    """
    if (p1[0] - p2[0]) == 0:
        return -float("inf")
    else:
        return (p1[1] - p2[1]) / (p1[0] - p2[0])


def calc_bias(p1, p2):
    """
    Calculate bias for a line between two points

    Args:
        p1 (tuple [2]): Point with x and y coordinate
        p2 (tuple [2]): Point with x and y coordinate

    Returns:
        Bias (Float)

    """
    if (p1[0] == p2[0]):
        return 0
    return (p1[1] * p2[0] - p2[1] * p1[0]) / (p2[0] - p1[0])


def calc_frame_pos(p):
    """
    Determines the position of the point p on the frame (left, top, right, bot) -> (0, 1, 2, 3)

    Args:
        p (tuple [2]): Point with x and y coordinate on frame

    Returns:
        fidx (int): frame border index

    """
    if p[0] == left:
        frame_pos_p = 0
    elif p[1] == top:
        frame_pos_p = 1
    elif p[0] == right:
        frame_pos_p = 2
    elif p[1] == bot:
        frame_pos_p = 3
    else:
        raise ValueError(f"First point declared {p[0], p[1]} not on frame.")
    return frame_pos_p


def calc_target_point_rect(p1, p2):
    """
    Calculates the target point on the other side of a rectangular frame

    Args:
        p1 (tuple [2]): Point with x and y coordinate (outer point on frame)
        p2 (tuple [2]): Point with x and y coordinate (inner point within frame)

    Returns:
        tp (tuple [2]): Target point

    """
    tp = [0, 0]                 # coordinates of target point
    # determine position on frame of p1
    frame_pos_p1 = calc_frame_pos(p1)

    # opposite border position
    frame_pos_opp = (frame_pos_p1 + 2) % 4

    # handle vertical lines, because steepness is infinity
    if p1[0] == p2[0]:
        tp[0] = p1[0]
        tp[1] = frame_borders[frame_pos_opp]
        return tp
    # otherwise calculate line equation y = mx + b
    m = calc_steepness(p1, p2)
    b = calc_bias(p1, p2)
    # if left or right
    if frame_pos_p1 % 2 == 0:
        tp[0] = frame_borders[frame_pos_opp]
        tp[1] = m * frame_borders[frame_pos_opp] + b
        if tp[1] < top:
            tp[0] = (top - b) / m
            tp[1] = top
        elif tp[1] > bot:
            tp[0] = (bot - b) / m
            tp[1] = bot
    # if top or bottom
    else:
        tp[0] = (frame_borders[frame_pos_opp] - b) / m
        tp[1] = frame_borders[frame_pos_opp]
        if tp[0] < left:
            tp[0] = left
            tp[1] = m * left + b
        elif tp[0] > right:
            tp[0] = right
            tp[1] = m * right + b
    return tp


def calc_lines(outer_points, inner_points):
    """
    Calculates each line to draw and from that each edge in the pattern

    Args:
        outer_points (tuple[n, 2]): tuple containing n points of dimension 2 on frame
        inner_points (tuple[n, 2]): tuple containing n points of dimension 2 within frame

    Returns:
        lines (list of line objects): The list containing all lines on and within the frame
        to be drawn on canvas. The line objects contain every intersection with another line
        an are sorted by their x coordinate, if its a non vertical line. Else by y coordinate.

    """
    # First add lines on outer frame
    lines = [Line((left, top), (left, bot)), Line((left, top), (right, top)),
             Line((right, top), (right, bot)), Line((left, bot), (right, bot))]
    for op in outer_points:
        for ip in inner_points:
            # Determine target point
            tp = calc_target_point_rect(op, ip)
            # Check if that line is already in the line list
            if all(not line.contains_same_points(op, tp) for line in lines):
                new_line = Line(op, tp)
                new_line.add_point(ip)
                # Add target point to frame line (intersection with frame)
                frame_pos_tp = calc_frame_pos(tp)
                lines[frame_pos_tp].add_point(tp)
                # Check for intersections with other lines within the frame
                for inner_line in lines[4:]:
                    intersection = new_line.calc_intersection(inner_line)
                    if intersection and point_is_within_frame(intersection):
                        new_line.add_point(intersection)
                        inner_line.add_point(intersection)
                lines.append(new_line)
    for line in lines:
        # sort points in lines from left to right, except vertical lines (from top to bottom)
        if line.points[0][0] == line.points[1][0]:
            line.points.sort(key=lambda p: p[1])
        else:
            line.points.sort(key=lambda p: p[0])

    return lines


def calc_edges(outer_points, inner_points):
    """
    Calculates a full list of edges in the pattern

    Args:
        outer_points (tuple[n, 2]): tuple containing n points of dimension 2 on frame
        inner_points (tuple[n, 2]): tuple containing n points of dimension 2 within frame

    Returns:
        edges (list of edge objects)

    """
    edges = []
    lines = calc_lines(outer_points, inner_points)
    for line in lines:
        for i in range(len(line.points) - 1):
            edges.append(Edge(line.points[i], line.points[i+1], line.m))
    return edges


def calc_area(start_edge, target_point, direction, edges):
    """
    Calculates an area (list of points) that is determined by the starting
    edge, -point and direction

    Args:
        start_edge (Edge object): The starting edge
        target_point (tuple [2]): The target point
        direction (int): Turning direction. 1 for clockwise, -1 for anti-clockwise
        edges (list of edge objects): The list of edges in the pattern

    Returns:
        area (tuple of edges, points): if the creation is possible it returns the edges
            with point the edge is pointing to in the area given the start parameter,
            but False if the given start_edge, point and direction do not match
            if its an edge on the frame.

    """
    area = [(start_edge, target_point)]
    start_point = start_edge.get_other_point(target_point)
    last_edge = start_edge
    last_point = target_point
    last_angle = 0
    # Check if the given edge is an edge on the frame an the given direction is possible.
    if start_edge.is_frame_edge() >= 0:
        if not (start_edge.is_viable_direction(
                start_edge.is_frame_edge(), target_point, direction)):
            return False
    while not (last_point == start_point):
        # Fill a list containing all edges containing last_point and sort it by its steepness m
        edges_containing_last_point = []
        for edge in edges:
            if edge.contains_point(last_point):
                edges_containing_last_point.append(edge)
        # get index of last_edge in list by angle comparison
        edges_containing_last_point.sort(
            key=lambda edge: edge.calc_vector_angle(last_point))
        last_angle = last_edge.calc_vector_angle(last_point)
        last_edge_idx = [i for i in range(len(edges_containing_last_point))
                         if edges_containing_last_point[i].calc_vector_angle(last_point)
                         == last_angle][0]
        # updating last edge and last point
        last_edge = edges_containing_last_point[(
            last_edge_idx - direction) % len(edges_containing_last_point)]
        last_point = last_edge.get_other_point(last_point)
        area.append((last_edge, last_point))
    return area


def calc_areas(outer_points, inner_points):
    """
    Calculates a full list of areas in the pattern.

    Args:
        outer_points (tuple[n, 2]): tuple containing n points of dimension 2 on frame
        inner_points (tuple[n, 2]): tuple containing n points of dimension 2 within frame

    Returns:
        areas (list of area objects)

    """
    edges = calc_edges(outer_points, inner_points)
    # Contains edges that are checked clockwise with an angle >= 0 (positive)
    # or anticlockwise with < 0.
    edges_checked_c_p = deque()
    # And vice versa
    edges_checked_ac_p = deque()
    # list of edges which are yet to check with orientation (or point it is pointing to)
    edges_to_check = {(edges[0], edges[0].p2)}
    areas = []
    # Try with the first edge in the list clockwise rotation to check if this direction is viable
    if calc_area(edges[0], edges[0].p2, 1, edges):
        direction = 1
    else:
        direction = -1
    # Continue with adding areas to the list until the edges_to_check set is empty
    area_index = 0
    # while edges_to_check:
    for _ in range(5):
        edge_to_check, point_to_check = edges_to_check.pop()
        print(f"Area {area_index:}")
        print(
            f"edge_to_check: {str(edge_to_check)}, pointing to: {point_to_check}")
        if direction == 1:
            print("clockwise")
        else:
            print("anticlockwise")
        # If the edge was already checked in that direction, continue
        if edge_to_check.is_cp(point_to_check, direction):
            if edge_to_check in edges_checked_c_p:
                continue
        else:
            if edge_to_check in edges_checked_ac_p:
                continue
        area = calc_area(edge_to_check, point_to_check, direction, edges)
        # add edges to the "checked" lists
        print(f"calculated area: ")
        for edge, point in area:
            print(point, end="\t")
            if edge.is_cp(point, direction):
                edges_checked_c_p.append(edge)
            else:
                edges_checked_ac_p.append(edge)
            # add edges from the calculated area to the edges_to_check set
            if edge != edge_to_check:
                edges_to_check.add((edge, point))
        print("\n")
        direction *= -1
        areas.append((area, area_index))
        area_index += 1

    return areas


outer_points = [(left, top), (left, bot)]  # , (right, top), (right, bot)]
for point in outer_points:
    draw_point(point)

# inner_points = [(600, 500), (400, 500), (500, 400), (500, 600)]
# inner_points = [(400, 500), (600, 500)]
inner_points = [(400, 500), (600, 500)]
for point in inner_points:
    draw_point(point, fillcolor="orange")


for opoint in outer_points:
    for ipoint in inner_points:
        draw_line_within_frame(opoint, ipoint)


# ugly debugging prints

tki.mainloop()
