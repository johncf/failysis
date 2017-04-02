#!/bin/python

import csv
from utils import read_csv, write_csv, failure_rate

def main(cfails_file, obspop_file, outfile='/tmp/plot.svg', type_='plot', explain=False):
    # read input files
    fail_xs, fail_ys = read_csv(cfails_file)
    obs_xs, obs_ys = read_csv(obspop_file)

    # calculate failure rate
    xs, fr_ys, (f_ys, f_dydxs, o_ys) = failure_rate((fail_xs, fail_ys), (obs_xs, obs_ys))

    if type_ == 'csv':
        # output result as csv and return
        write_csv(xs, fr_ys, outfile)
        print("Written failure rate values to", outfile)
        return

    # plot result
    import matplotlib.pyplot as plt
    #from mpl_toolkits.axes_grid1 import host_subplot
    #import mpl_toolkits.axisartist as AA
    if explain:
        fig, (ax2, ax) = plt.subplots(2, 1)
        fig.set_size_inches(8, 7)

        #ax1.set_ylabel("Cumulative failures")
        #ax1.set_xlim(-2e3, 62e3)
        #ax1.set_ylim(0, 4800)
        #ax1.plot(xs, f_ys, 'b-')

        ax2.set_ylabel("Derivative of cumulative failures (#/hr)")
        ax2.set_xlabel("Power-on hours")
        ax2.set_yscale("log")
        ax2.set_ylim(1e-4, 1)
        ax2.plot(xs, f_dydxs, 'r-')

        ax3 = ax2.twinx()
        ax3.set_ylabel("Number of disks under observation")
        ax3.set_yscale("log")
        ax3.set_ylim(90, 1e5)
        ax3.fill_between(xs, o_ys, 90, color='#0766aa33')

        red, blue, nil = '#bb0000', '#11448899', '#00000000'
        ax2.tick_params(axis='y', colors=red)
        ax2.spines["left"].set_color(red)
        ax2.spines["right"].set_color(nil)
        ax3.tick_params(axis='y', colors=blue)
        ax3.spines["left"].set_color(nil)
        ax3.spines["right"].set_color(blue)
    else:
        fig, ax = plt.subplots()
        fig.set_size_inches(8, 4)

    ax.set_xlabel("Power-on years")
    ax.set_ylabel("Normalized AFR (#/yr)")
    ax.set_yscale("log")
    ax.set_ylim(1e-3, 2)
    ax.plot(xs/24/365, fr_ys*24*365)

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
    parser.add_argument('-t', metavar='TYPE', choices=['csv', 'image'], default='image',
                        help='output type (default: image)')
    parser.add_argument('-x', '--explain', action='store_true',
                        help='include intermediate steps in the plot')
    args = parser.parse_args()
    main(args.cumufails, args.obspop, outfile=args.o, type_=args.t, explain=args.explain)