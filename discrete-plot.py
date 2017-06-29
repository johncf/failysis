#!env python3

import csv
from utils import *

bin_width = 0.25
samples_per_bin = 20 * bin_width
bar_fontsize = None

def bar(ax, xs, ys, width, color, label=None, text_f=lambda y: int(np.round(y))):
    ax.bar(xs, ys, width=width, align='edge', color=color, label=label)
    for i, (x, y) in enumerate(zip(xs, ys)):
        #if i % 2 == 0:
            ax.text(x + width/2, y, text_f(y), ha='center', va='bottom', fontsize=bar_fontsize)

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
    fig, (ax1, ax2, ax) = plt.subplots(3, 1, sharex=True)
    fig.set_size_inches(5.3, 8)
    ax.set_xlim(-0.25, 7.25)

    ax1.set_ylabel("# failures")
    #ax1.set_ylim(0, 4800)
    ax1.plot(fail_xs, fail_ys, color='#cc5511', label='Cumulative number of failures')
    bar(ax1, fdelta_xs, fdelta_ys, bin_width, color='#cc880088', label='Number of failures in-between')
    ax1.legend()

    ax2.set_ylabel("Disk-years observed")
    ax2.set_yscale("log")
    ax2.set_ylim(90, 1e5)
    #ax2.plot(obs_xs, obs_ys, label='Number of disks observed')
    bar(ax2, disk_hrs_xs, disk_hrs_ys, bin_width, color='#0044ff55', label='Disk-years observed')
    #ax2.legend()

    ax.set_xlabel("Power-on years")
    ax.set_ylabel("AFR (%)")
    ax.set_yscale("log")
    ax.set_ylim(2e-1, 80)
    #ax.plot(xs, 100*fr_ys, color='#ff1100')
    fr_discrete_ys = fdelta_ys/disk_hrs_ys
    bar(ax, disk_hrs_xs, 100*fr_discrete_ys, bin_width, color='#ff440055', text_f=lambda y: np.round(y, 1) if y < 10 else int(np.round(y)))

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
                        help='output plot to %(metavar)s (default: /tmp/out.svg)')
    args = parser.parse_args()
    main(args.cumufails, args.obspop, outfile=args.o)
