#!/bin/python

import csv
from utils import *

bin_width = 0.5
samples_per_bin = 20 * bin_width

def main(cfails_file, obspop_file, outfile='/tmp/plot.svg'):
    # read input files
    fail_xs, fail_ys = read_csv(cfails_file)
    obs_xs, obs_ys = read_csv(obspop_file)

    fail_xs /= 24*365
    obs_xs /= 24*365
    x_lims = shortest_common_limits(fail_xs, obs_xs)

    disk_hours_bins = binned_integral(obs_xs, obs_ys, bin_width, samples_per_bin, x_lims)
    fails_delta_bins = binned_non_decreasing_delta(fail_xs, fail_ys, bin_width, x_lims)
    disk_hrs_xs, _, disk_hrs_ys = unzip(disk_hours_bins)
    fdelta_xs, _, fdelta_ys = unzip(fails_delta_bins)
    xs, fr_ys, _ = failure_rate((fail_xs, fail_ys), (obs_xs, obs_ys))

    # plot result
    import matplotlib.pyplot as plt
    fig, (ax1, ax2, ax) = plt.subplots(3, 1)
    fig.set_size_inches(8, 10)

    ax1.set_ylabel("Number of failures")
    #ax1.set_xlim(-2e3, 62e3)
    ax1.set_ylim(0, 4800)
    ax1.plot(fail_xs, fail_ys, color='#cc5511', label='Cumulative')
    ax1.bar(fdelta_xs, fdelta_ys, width=bin_width, align='edge', color='#cc880088', label='Yearly deltas')
    for x, y in zip(fdelta_xs, fdelta_ys):
        ax1.text(x + bin_width/2, y, np.round(y).astype(int), ha='center', va='bottom')
    ax1.legend()

    ax2.set_ylabel("Number observed")
    ax2.set_yscale("log")
    ax2.set_ylim(90, 1e5)
    ax2.plot(obs_xs, obs_ys, label='Number of disks observed')
    ax2.bar(disk_hrs_xs, disk_hrs_ys, width=bin_width, align='edge', color='#0044ff55', label='Number of disk-years observed')
    for x, y in zip(disk_hrs_xs, disk_hrs_ys):
        ax2.text(x + bin_width/2, np.exp(np.log(y) + 0.2), np.round(y).astype(int), ha='center', va='bottom')
    ax2.legend()

    ax.set_xlabel("Power-on years")
    ax.set_ylabel("Normalized AFR (#/yr)")
    ax.set_yscale("log")
    ax.set_ylim(1e-3, 2)
    ax.plot(xs, fr_ys, color='#ff1100')
    fr_discrete_ys = fdelta_ys/disk_hrs_ys
    ax.bar(disk_hrs_xs, fr_discrete_ys, width=bin_width, align='edge', color='#ff440055')
    for x, y in zip(disk_hrs_xs, fr_discrete_ys):
        ax.text(x + bin_width/2, np.exp(np.log(y) + 0.2), np.round(y, 2).astype(str), ha='center', va='bottom')

    fig.tight_layout()
    fig.savefig(outfile, bbox_inches="tight")
    print("Written failure rate plot to", outfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute failure rate distribution over '
                        'a parameter (such as power-on hours), given the cumulative failures '
                        'and observed population over it.')
    parser.add_argument('cumufails', metavar='CUMUFAILS', help='cumulative failures (csv file)')
    parser.add_argument('obspop', metavar='OBSPOP', help='observed population (csv file)')
    parser.add_argument('-o', metavar='FILE', default='/tmp/plot.svg',
                        help='output failure rate to %(metavar)s in the specified format')
                             #'Use any file type supported by matplotlib.')
    args = parser.parse_args()
    main(args.cumufails, args.obspop, outfile=args.o)
