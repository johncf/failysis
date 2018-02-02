#!/bin/env python3

from utils import read_csv, write_csv, failure_rate

def main(cfails_file, obspop_file, outfile='/tmp/plot.svg', type_='plot', title='', explain=False, ymax=16):
    # read input files
    fail_xs, fail_ys = read_csv(cfails_file)
    obs_xs, obs_ys = read_csv(obspop_file)

    # power-on hours to power-on years
    fail_xs /= 24*365
    obs_xs /= 24*365

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
        fig, (ax2, ax) = plt.subplots(2, 1, sharex=True, figsize=(7, 6),
                                      gridspec_kw={'height_ratios': [3, 4]})

        #ax2.set_ylabel("")
        #ax2.set_xlabel("Power-on years")
        ax2.set_yscale("log")
        ax2.set_ylim(2, 2e6)
        ax2.plot(xs, f_dydxs, 'crimson', label="rate of failures (disks/yr)")
        ax2.fill_between(xs, o_ys, 1, color='#0766aa33', label="disks observed")
        ax2.legend()
    else:
        fig, ax = plt.subplots(figsize=(8, 4))

    ax.set_xlabel("Age (power-on years)")
    ax.set_ylabel("Failure Rate (%/year)")
    #ax.set_yscale("log")
    ax.set_ylim(0, ymax)
    ax.plot(xs, fr_ys*100, 'chocolate')

    fig.tight_layout()
    if len(title) > 0:
        st = fig.suptitle(title)
        st.set_y(0.95)
        fig.subplots_adjust(top=0.9)

    fig.savefig(outfile, bbox_inches="tight")
    print("Written failure rate plot to", outfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute failure rate distribution over '
                        'power-on hours, given the cumulative failures '
                        'and observed population over it.')
    parser.add_argument('cumufails', help='cumulative failures (csv file)')
    parser.add_argument('obspop', help='observed population (csv file)')
    parser.add_argument('-o', metavar='imgfile', default='/tmp/plot.svg',
                        help='output failure rate to %(metavar)s in the specified format')
                             #'Use any file type supported by matplotlib.')
    parser.add_argument('-t', metavar='type', choices=['csv', 'image'], default='image',
                        help='output type (default: image)')
    parser.add_argument('-T', metavar='title', default='', help='Plot title')
    parser.add_argument('-x', '--explain', action='store_true',
                        help='include intermediate steps in the plot')
    parser.add_argument('--ylimit-max', dest='ymax', default=16, type=int,
                        help='y-axis max (default: 16)')
    args = parser.parse_args()
    main(args.cumufails, args.obspop, outfile=args.o, type_=args.t, title=args.T, explain=args.explain, ymax=args.ymax)
