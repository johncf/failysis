from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
import numpy as np
import csv

def read_csv(csvfile):
    xs, ys = [], []
    with open(csvfile, 'r') as file_:
        reader = csv.reader(file_, delimiter=',')
        for row in reader:
            xs.append(float(row[0]))
            ys.append(float(row[1]))
    return xs, ys

def write_csv(xs, ys, csvfile):
    with open(csvfile, 'w') as file_:
        writer = csv.writer(file_, quoting=csv.QUOTE_MINIMAL)
        for row in zip(xs, ys):
            writer.writerow(row)

def savgol_fit(xs, ys, samples, window_size, poly_order, x_lims=None, dydx=False):
    # linear interpolation function
    itp_f = interp1d(xs, ys, kind="linear")

    if x_lims is None:
        x_min, x_max = xs.min(), xs.max()
    else:
        x_min, x_max = x_lims

    # linearly spaced x values between x_min and x_max
    xs_lin = np.linspace(x_min, x_max, num=samples)

    # smooth
    ys_sg = savgol_filter(itp_f(xs_lin), window_size, poly_order)
    if dydx:
        dydx_sg = savgol_filter(itp_f(xs_lin), window_size, poly_order, deriv=1)
        dydx_sg /= (x_max - x_min) / samples # correct for x spacing
    else:
        dydx_sg = None

    return xs_lin, ys_sg, dydx_sg

def failure_rate(cfails, obspop, num_samples=2000, window_size=169, poly_order=3):
    cfails_xs, cfails_ys = np.array(cfails[0]), np.array(cfails[1])
    obspop_xs, obspop_ys = np.array(obspop[0]), np.array(obspop[1])
    x_lims = (max(1., cfails_xs.min(), obspop_xs.min()),
              min(cfails_xs.max(), obspop_xs.max()))

    f_xs, f_ys, f_dydxs = savgol_fit(cfails_xs, cfails_ys, num_samples, window_size, poly_order, x_lims, dydx=True)
    o_xs, o_ys, _ = savgol_fit(obspop_xs, obspop_ys, num_samples, window_size, poly_order, x_lims, dydx=False)

    # since the same x_lims and num_samples are passed, xs should be equal
    assert np.array_equal(f_xs, o_xs)

    fr_ys = f_dydxs/o_ys # element-wise division
    return f_xs, fr_ys, (f_ys, f_dydxs, o_ys)
