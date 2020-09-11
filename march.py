import numpy as np
import lookup
from tqdm import tqdm

def isosurface(func):
    # Wrapper function
    def inner_func(p):
        x, y, z = p
        return func(x, y, z)
    return inner_func

@isosurface
def func(x, y, z):
    #return x**2 + y**2 + z**2
    return (np.sqrt(x**2 + y**2) - 0.6)**2 + z**2


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


# Make bounding box
box = np.mgrid[-1:1:21j,-1:1:21j,-1:1:21j]
_, step_x, step_y, step_z = box.shape

delta = 0.2
isolevel = 0.4**2

vs = {}
faces = []

for i in range(step_x - 1):
    for j in range(step_y - 1):
        for k in range(step_z - 1):
            cube = box[:, i, j, k]
            cube = cube + inc * delta
            val = np.apply_along_axis(func, 1, cube)
            tri = get_triangles(cube, val, isolevel)
            if tri is not None:
                for t in tri:
                    vid_list = []
                    for v in t:
                        v = tuple(v)
                        if v not in vs:
                            vs[v] = len(vs) + 1
                        vid_list.append(vs[v])
                    faces.append(vid_list)

with open('torus.obj', 'w') as file:
    for v in vs:
        v = [str(x) for x in v]
        file.write('v ' +  ' '.join(v) + '\n')
    file.write('\n')
    for f in faces:
        f = [str(x) for x in f]
        file.write('f ' + ' '.join(f) + '\n')

