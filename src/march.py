import numpy as np
from . import lookup


"""         
                     4
            [4]--------------[5]
            /|               /|
          7/ |             5/ |
          / 8|    6       /   |9
        [7]--------------[6]  |
         |   |            |   |
         |  [0] ----------|--[1]
      11 |  /       0     |10/
         | / 3            | /  1
         |/               |/
        [3]--------------[2]
                 2

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
    step_x = int((x_max - x_min) / delta)
    step_y = int((y_max - y_min) / delta)
    step_z = int((z_max - z_min) / delta)
    box = np.mgrid[x_min:x_max:(step_x+1)*1j,y_min:y_max:(step_y+1)*1j,z_min:z_max:(step_z+1)*1j]
    return box

def march(func, isolevel, ranges, delta):
    # get bounding box
    x_range, y_range, z_range = ranges
    box = get_bbox(x_range, y_range, z_range, delta)
    _, step_x, step_y, step_z = box.shape
    # the marching cube
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

    # vertices and faces list
    vs = {}
    fs = []

    for i in range(step_x):
        for j in range(step_y):
            for k in range(step_z):
                cube = box[:, i, j, k] + inc * delta
                val = np.apply_along_axis(func, 1, cube)
                tri = get_triangles(cube, val, isolevel)
                if tri is None:
                    continue
                for t in tri:
                    vid_list = []
                    for v in t:
                        v = tuple(v)
                        if v not in vs:
                            vs[v] = len(vs) + 1
                        vid_list.append(vs[v])
                    fs.append(vid_list)
    return vs, fs

def write_obj(vs, fs, filename):
    with open(filename, 'w') as file:
        file.write("# --- Vertices ---\n")
        for v in vs:
            v = [str(x) for x in v]
            file.write('v ' +  ' '.join(v) + '\n')
        file.write("# --- Faces ---\n")
        for f in fs:
            f = [str(x) for x in f]
            file.write('f ' + ' '.join(f) + '\n')
