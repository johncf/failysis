#!/bin/env python3

import matplotlib.pyplot as plt
import json

from utils import *

def main(opts_json, plotfile):
    with open(opts_json, 'r') as file_:
        opts = json.load(file_)

    fig, ax = plt.subplots()

    ax.set_xlabel("Power-on hours")
    ax.set_ylabel("AFR (%)")

    ax.set_xlim(-0.2, 7.2)
    #ax.set_ylim(2e-2, 2e2)
    #ax.set_yscale("log")
    ax.set_ylim(0, 40)

    for subpop in opts['data']:
        fail_xs, fail_ys = read_csv(subpop['cumu-fails'])
        obs_xs, obs_ys = read_csv(subpop['obs-pop'])
        fail_xs /= 24*365
        obs_xs /= 24*365
        xs, fr_ys, _ = failure_rate((fail_xs, fail_ys), (obs_xs, obs_ys))
        ax.plot(xs, fr_ys*100, label=subpop['label'])

    ax.legend()
    ax.grid(b=True, which='major', linestyle='--')

    #fig.suptitle(opts['title'])
    fig.set_size_inches(5.3, 3)
    fig.savefig(plotfile, bbox_inches="tight")
    print("Written failure rate plot to", plotfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('metadata', metavar='METADATA', help='JSON file describing input data')
    parser.add_argument('-o', metavar='FILE', default='/tmp/plot.svg',
                        help='output plot to %(metavar)s (default: /tmp/out.svg)')
    args = parser.parse_args()
    main(args.metadata, plotfile=args.o)
