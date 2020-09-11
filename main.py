import src.march as march
import src.functions as functions

def main(func, isolevel, x_range, y_range, z_range, delta, out_file):
    vs, fs = march.march(func, isolevel, (x_range, y_range, z_range), delta)
    march.write_obj(vs, fs, out_file)
    
if __name__ == '__main__':

    delta = 0.05
    x_range = (-1, 1)
    y_range = (-1, 1)
    z_range = (-1, 1)

    isolevel = 0.3**2
    func = functions.torus(0.5)
    
    out_file = 'obj/torus_3.obj'

    main(func, isolevel, x_range, y_range, z_range, delta, out_file)
