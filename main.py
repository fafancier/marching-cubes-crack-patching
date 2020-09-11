import src.march as march
import src.functions as functions

def main(func, isolevel, x_range, y_range, z_range, delta, out_file):
    vs, fs = march.march(func, isolevel, (x_range, y_range, z_range), delta)
    march.write_obj(vs, fs, out_file)
    
if __name__ == '__main__':

    delta = 0.1
    x_range = (-2, 2)
    y_range = (-2, 2)
    z_range = (-2, 2)

    isolevel = 0.5**2
    func = functions.torus(1)
    
    out_file = 'obj/torus_3.obj'

    main(func, isolevel, x_range, y_range, z_range, delta, out_file)
