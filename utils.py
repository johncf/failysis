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

# calculates the integral of ys over xs for each bin
def binned_integral(xs, ys, bin_width, samples_per_bin, x_lims=None):
    x_min, x_max = x_lims if x_lims is not None else xs.min(), xs.max()

    bin_start = np.floor(x_min / bin_width) * bin_width
    if np.abs(bin_start - x_min) > bin_width:
        bin_start = x_min

    y_itp = interp1d(xs, ys, kind="linear")

    bins = []
    num_bins = int(np.ceil((x_max - bin_start) / bin_width))
    for i in range(num_bins):
        left = bin_start + bin_width*i
        right = bin_start + bin_width*(i+1)
        sample_halfwidth = (right - left) / samples_per_bin / 2
        xs_new = np.linspace(left + sample_halfwidth, right - sample_halfwidth, num=samples_per_bin)
        xs_lims_mask = np.logical_and(np.less_equal(left, xs_new), np.less_equal(xs_new, right))
        ys_new = y_itp(xs_new) * xs_lims_mask.astype(np.float32)
        bins.push((left, right, np.sum(ys_new) / samples_per_bin))
    return bins

# calculate y-deltas between the left and right of each bin in a non-decreasing function
def binned_non_decreasing_delta(xs, ys, bin_width, x_lims=None):
    x_min, x_max = x_lims if x_lims is not None else xs.min(), xs.max()

    bin_start = np.floor(x_min / bin_width) * bin_width
    if np.abs(bin_start - x_min) > bin_width:
        bin_start = x_min

    y_itp = interp1d(xs, ys, kind="linear")

    bins = []
    num_bins = int(np.ceil((x_max - bin_start) / bin_width))
    for i in range(num_bins):
        left = bin_start + bin_width*i
        right = bin_start + bin_width*(i+1)
        y_left = y_itp(max(left, x_min))
        y_right = y_itp(min(right, x_max))
        bins.push((left, right, y_right - y_left))
    return bins

def savgol_fit(xs, ys, samples, window_size, poly_order, x_lims=None, dydx=False):
    # linear interpolation function
    y_itp = interp1d(xs, ys, kind="linear")

    x_min, x_max = x_lims if x_lims is not None else xs.min(), xs.max()

    # linearly spaced x values between x_min and x_max
    xs_new = np.linspace(x_min, x_max, num=samples)

    # smooth
    ys_sg = savgol_filter(y_itp(xs_new), window_size, poly_order)
    if dydx:
        dydx_sg = savgol_filter(y_itp(xs_new), window_size, poly_order, deriv=1)
        dydx_sg /= (x_max - x_min) / samples # correct for x spacing
    else:
        dydx_sg = None

    return xs_new, ys_sg, dydx_sg

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
