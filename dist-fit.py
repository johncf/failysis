#!/bin/env python3

from scipy.stats import weibull_min as weibull, gamma, lognorm
from scipy.optimize import curve_fit
from utils import read_csv, write_csv, failure_rate
import matplotlib.pyplot as plt
import matplotlib.colors as cm
import numpy as np

def main(cfails_file, obspop_file, outfile='/tmp/plot.svg', scale='normal'):
    # read input files
    fail_xs, fail_ys = read_csv(cfails_file)
    obs_xs, obs_ys = read_csv(obspop_file)

    # power-on hours to power-on years
    fail_xs /= 24*365
    obs_xs /= 24*365

    # calculate failure rate
    xs, fr_ys, (_, _, o_ys) = failure_rate((fail_xs, fail_ys), (obs_xs, obs_ys))

    xs_s, ys_s, o_ys_s = sanitize(xs, fr_ys, o_ys)
    sig = sigma(o_ys_s)

    #fig, (ax, ax2) = plt.subplots(2, 1, sharex=True)
    #fig.set_size_inches(8, 8)
    #ax2.set_ylabel("Uncertainty (sigma)")
    #ax2.plot(xs_s, sig)

    fig, ax = plt.subplots()
    fig.set_size_inches(5.3, 3)

    ax.set_xlabel("Power-on years")
    ax.set_ylabel("AFR (%)")
    if scale == 'log':
        ax.set_yscale("log")
        ax.set_xscale("log")
        ax.set_ylim(1e-1, 1e2)
        ax.set_xlim(1e-1, 20)
    else:
        ax.set_ylim(0, 30)
    norm = cm.PowerNorm(0.5, vmin=0, vmax=np.max(sig))
    ax.scatter(xs_s, ys_s*100, c=sig, cmap='plasma', norm=norm, marker='.', s=0.5, label='raw')

    # for legend
    #ax.scatter(np.linspace(0.2,0.74,25), 5*np.ones(25), c=np.linspace(0, 1, 25), cmap='plasma', marker='.', s=0.5)

    for dist in ['weibull', 'gamma', 'lognorm']:
        params, covars = fit(dist, xs_s, ys_s, sig)
        xs_fit = np.linspace(0, 20, 1000)
        ys_fit = gen_ys(dist, params, xs_fit)
        ax.plot(xs_fit, ys_fit*100, label=dist)
        err = np.sum(np.square(gen_ys(dist, params, xs_s) - ys_s)/np.square(sig))
        print(dist, params, np.sqrt(np.diag(covars)), err)

    ax.legend()
    fig.savefig(outfile, bbox_inches="tight")

def sigma(weights):
    """ returns uncertainties based on weights """
    probs = weights / np.max(weights)
    sigma = 1 / np.sqrt(probs)
    return sigma

def sanitize(xs, ys, os):
    assert(len(xs) == len(ys) and len(xs) == len(os))
    # remove negative entries
    le0i = np.where(ys <= 0) # array of indices
    xs = np.delete(xs, le0i)
    ys = np.delete(ys, le0i)
    os = np.delete(os, le0i)
    return xs, ys, os

def fit(dist, xs, ys, sig=None):
    """ returns a dictionary of parameters """
    if dist == 'weibull':
        h = lambda x, c, sc: weibull.pdf(x, c, scale=sc) / weibull.sf(x, c, scale=sc)
    elif dist == 'gamma':
        h = lambda x, a, sc: gamma.pdf(x, a, scale=sc) / gamma.sf(x, a, scale=sc)
    elif dist == 'lognorm':
        h = lambda x, s, sc: lognorm.pdf(x, s, scale=sc) / lognorm.sf(x, s, scale=sc)
    else:
        raise ValueError("Invalid dist")
    return curve_fit(h, xs, ys, p0=[1, np.max(xs)], sigma=sig)

def gen_ys(dist, params, xs):
    """ returns ys corresponding to xs """
    p1 = params[0]
    sc = params[1]
    if dist == 'weibull':
        f = lambda x: weibull.pdf(x, p1, scale=sc) / weibull.sf(x, p1, scale=sc)
    elif dist == 'gamma':
        f = lambda x: gamma.pdf(x, p1, scale=sc) / gamma.sf(x, p1, scale=sc)
    elif dist == 'lognorm':
        f = lambda x: lognorm.pdf(x, p1, scale=sc) / lognorm.sf(x, p1, scale=sc)
    else:
        raise ValueError("Invalid dist")
    return np.vectorize(f)(xs)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute failure rate distribution over '
                        'power-on hours, given the cumulative failures '
                        'and observed population over it.')
    parser.add_argument('cumufails', metavar='CUMUFAILS', help='cumulative failures (csv file)')
    parser.add_argument('obspop', metavar='OBSPOP', help='observed population (csv file)')
    parser.add_argument('-o', metavar='FILE', default='/tmp/plot.svg',
                        help='output failure rate plots to %(metavar)s')
    parser.add_argument('--scale', metavar='TYPE', default='normal',
                        help='scale used when fitting (choices: normal, log)')
    args = parser.parse_args()
    main(args.cumufails, args.obspop, outfile=args.o, scale=args.scale)
