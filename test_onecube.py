import numpy
import numpy as np
from src import lookup
import src.functions as functions
import src.march as march

"""         
             z
             |
             |      4
            [4]--------------[5]
            /|               /|
          7/ |             5/ |
          / 8|    6       /   |9
        [7]--------------[6]  |
         |   |            |   |
         |  [0] ----------|--[1]---- y
      11 |  /       0     |10/
         | / 3            | /  1
         |/               |/
        [3]--------------[2]
       /         2
      /
     x

"""


def get_topology(gridval, isovalue):
    assert len(gridval) == 8
    pow2 = 2 ** np.arange(8)
    inside = (gridval < isovalue).astype(np.int)
    top_id = np.sum(inside * pow2)
    return top_id


def get_edge_cut(grid, gridval, top_id, isovalue):
    edges = lookup.EDGE_TABLE[top_id]
    if edges == 0:
        return None
    # 12 edges
    cuts = np.zeros((12, 3))
    for i in range(12):
        if edges & (1 << i):
            p1, p2 = lookup.EDGE_VERTEX[i]
            cuts[i] = vertex_interpolate(grid[p1], grid[p2], gridval[p1], gridval[p2], isovalue)
    return cuts


def vertex_interpolate(p1, p2, v1, v2, isovalue):
    if np.any(p1 > p2):
        p1, p2, v1, v2 = p2, p1, v2, v1
    p = p1
    if np.abs(v1 - v2) > 1e-5:
        p = p1 + (p2 - p1) * (isovalue - v1) / (v2 - v1)
    return p


def get_triangles(grid, gridval, isovalue):
    top_id = get_topology(gridval, isovalue)
    edge_cut = get_edge_cut(grid, gridval, top_id, isovalue)
    if edge_cut is None:
        return None
    tri_edges = lookup.TRI_TABLE[top_id] + [-1, -1]
    tri_edges = [tri_edges[3 * i:3 * i + 3] for i in range(len(tri_edges) // 3)]
    triangles = [edge_cut[e] for e in tri_edges if e[0] >= 0]
    triangles = np.stack(triangles)
    return triangles


def get_bbox(x_range, y_range, z_range, delta):
    x_min, x_max = x_range
    y_min, y_max = y_range
    z_min, z_max = z_range
    step_x = int((x_max - x_min + 1e-6) / delta)
    step_y = int((y_max - y_min + 1e-6) / delta)
    step_z = int((z_max - z_min + 1e-6) / delta)
    box = np.mgrid[x_min:x_max:(step_x + 1) * 1j, y_min:y_max:(step_y + 1) * 1j, z_min:z_max:(step_z + 1) * 1j]
    return box


def write_obj(vs, fs, filename):
    with open(filename, 'w') as file:
        file.write("# --- Vertices ---\n")
        for v in vs:
            v = [str(x) for x in v]
            file.write('v ' + ' '.join(v) + '\n')
        file.write("# --- Faces ---\n")
        for f in fs:
            f = [str(x) for x in f]
            file.write('f ' + ' '.join(f) + '\n')


class Vertex():
    def __init__(self):
        self.pos = None
        self.value = 0
        self.vid = -1


class Edge():
    def __init__(self):
        self.v1 = -1
        self.v2 = -1
        self.eid = -1


class Cube():
    isolevel = 0.5 ** 2
    func = functions.torus(1)
    meter_per_voxel = 0.1
    # defination
    inc = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
        [0, 1, 1],
        [1, 1, 1],
        [1, 0, 1]
    ])

    def __init__(self, voxel_per_edge):
        self.iso_value = Cube.isolevel
        self.corner_values = np.zeros(8, np.float)
        self.corner_vertex_ids = np.zeros(8, np.int)
        self.edges = 12 * [Edge()]  # define by two vertex id
        self.vertexs = 8 * [Vertex()]  # define by two vertex id
        self.voxel_per_edge = voxel_per_edge
        self.edge_length = voxel_per_edge * Cube.meter_per_voxel
        self.cube_corners = None
        self.cube_corner_pos = None
        self.vs = {}
        self.fs = []
        self.edges_on_face = 6 * []

    def set_cube(self, cube_corners):
        self.cube_corners = cube_corners
        self.cube_corner_pos = np.array(np.round((cube_corners) / self.meter_per_voxel), np.int)

    def __getitem__(self, item):
        return self.cube_corners[item], self.cube_corner_pos[item]

    def marching_cube(self, save):
        self.corner_values = np.apply_along_axis(Cube.func, 1, self.cube_corners)
        tri = get_triangles(self.cube_corners, self.corner_values, Cube.isolevel)
        for v, value in zip(self.cube_corners, self.corner_values):
            color = [1, 0, 0]
            if value > Cube.isolevel:
                color = [0, 0, 1]
            v = tuple(np.r_[v, color])
            if v not in self.vs:
                self.vs[v] = len(self.vs) + 1
        if tri is None:
            return
        for t in tri:
            vid_list = []
            for v in t:
                v = tuple(np.r_[v, [0, 1, 0]])
                if v not in self.vs:
                    self.vs[v] = len(self.vs) + 1
                vid_list.append(self.vs[v])
            self.fs.append(vid_list)

        if save:
            out_name = str(self.cube_corner_pos[0]) + "_" + str(self.voxel_per_edge) + ".obj"
            write_obj(self.vs, self.fs, out_name)
            print(f"saving {out_name} ...")

    def find_fine_face(self):
        '''
        find all correspond fine cube face and copy their fine edge
        :return: 
        '''


if __name__ == "__main__":
    # vertices and faces list
    origin = [-1.6, -0.6, 0.0]
    two_large_cubes = {}
    # Two Cube
    voxel_per_edge = 2
    delta = voxel_per_edge * Cube.meter_per_voxel
    x_range = (origin[0], origin[0] + delta)
    y_range = (origin[1], origin[1])
    z_range = (origin[2], origin[2])

    box = get_bbox(x_range, y_range, z_range, delta)
    _, step_x, step_y, step_z = box.shape
    for i in range(step_x):
        for j in range(step_y):
            for k in range(step_z):
                cube_corners = box[:, i, j, k] + Cube.inc * delta
                c = Cube(voxel_per_edge)
                c.set_cube(cube_corners)
                if tuple(c.cube_corner_pos[0]) not in two_large_cubes:
                    two_large_cubes[tuple(c.cube_corner_pos[0])] = c
    for key, cube in two_large_cubes.items():
        cube.marching_cube(True)

    eight_small_cubes_in_left_cube = {}
    # Eight small cube in Left cube
    voxel_per_edge = 1
    delta = voxel_per_edge * Cube.meter_per_voxel
    x_range = (origin[0], origin[0] + delta)
    y_range = (origin[1], origin[1] + delta)
    z_range = (origin[2], origin[2] + delta)
    box = get_bbox(x_range, y_range, z_range, delta)
    _, step_x, step_y, step_z = box.shape
    for i in range(step_x):
        for j in range(step_y):
            for k in range(step_z):
                cube_corners = box[:, i, j, k] + Cube.inc * delta
                c = Cube(voxel_per_edge)
                c.set_cube(cube_corners)
                if tuple(c.cube_corner_pos[0]) not in eight_small_cubes_in_left_cube:
                    eight_small_cubes_in_left_cube[tuple(c.cube_corner_pos[0])] = c
    for key, cube in eight_small_cubes_in_left_cube.items():
        cube.marching_cube(True)
    pass
