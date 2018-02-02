#!/bin/env python3

from numpy import mean, trapz, linspace
from scipy.interpolate import interp1d
from utils import read_csv, useful_obs

def main(fails, obspop, minimal=False):
    # read input file
    obs_xs, obs_ys = useful_obs(*read_csv(obspop))
    diskyears = trapz(obs_ys, x=obs_xs/24/365)
    with open(fails, 'rb') as f:
        f.seek(-20, 2)
        failcount = int(f.readlines()[-1].decode().split(',')[1])
    mean_afr = failcount/diskyears*100
    obs_itp = interp1d(obs_xs, obs_ys, kind="linear")
    obs_linxs = linspace(obs_xs[0], obs_xs[-1], num=len(obs_xs))
    mean_dct = mean([obs_itp(x) for x in obs_linxs])
    useful_len = (obs_xs[-1] - obs_xs[0])/24/365
    if minimal:
        print("{:.0f} {} {:.2f}% {:.2f} {:.0f}".format(diskyears, failcount, mean_afr, useful_len, mean_dct))
    else:
        print("Total disk-years:", diskyears)
        print("Total failures:", failcount)
        print("Mean AFR: {}%".format(mean_afr))
        print("Useful length of observation:", useful_len)
        print("Mean number of disks over useful length:", mean_dct)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute basic statistics from failure and observation data.')
    parser.add_argument('fails', help='cumulative failures (csv file)')
    parser.add_argument('obsct', help='observed population (csv file)')
    parser.add_argument('-m', '--minimal', dest='m', action='store_true',
                        help='Just output numbers')
    args = parser.parse_args()
    main(args.fails, args.obsct, minimal=args.m)
