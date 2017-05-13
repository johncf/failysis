#!env python3

from scipy.stats import weibull_min as weibull, gamma, lognorm
from scipy.optimize import curve_fit
from utils import read_csv, write_csv, failure_rate
import matplotlib.pyplot as plt
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

    fig, ax = plt.subplots()
    fig.set_size_inches(8, 4)

    ax.set_xlabel("Power-on years")
    ax.set_ylabel("AFR (%)")
    ax.set_yscale("log")
    ax.set_ylim(2e-1, 80)

    # sample points from empirical failure rate curve based on observed population
    # otherwise, all points in our gets equal weightage during fitting
    xs_s, ys_s = sample(xs, fr_ys, o_ys)

    ax.scatter(xs_s, ys_s*100, marker='.', label='raw sampled')

    for dist in ['weibull', 'gamma', 'lognorm']:
        if scale == 'normal':
            params, covars = fit(dist, xs_s, ys_s)
        elif scale == 'log':
            params, covars = logfit(dist, xs_s, ys_s)
        else:
            raise ValueError("Invalid scale")
        ys_fit = gen_ys(dist, params, xs)
        ax.plot(xs, ys_fit*100, label=dist)
        print(dist, params, np.sqrt(np.diag(covars)))

    ax.legend()
    fig.savefig(outfile, bbox_inches="tight")

def sample(xs, ys, weights, max_samples=400):
    """ returns sampled xs and ys based on weights """
    probs = weights / np.sum(weights)
    si = np.sort(np.random.choice(len(weights), max_samples, replace=False, p=probs))
    xs = xs[si]
    ys = ys[si]

    # remove negative entries
    le0i = np.where(ys <= 0) # array of indices
    xs = np.delete(xs, le0i)
    ys = np.delete(ys, le0i)
    return xs, ys

def logfit(dist, xs, ys):
    """ returns a dictionary of parameters """
    if dist == 'weibull':
        logh = lambda x, c, sc: weibull.logpdf(x, c, scale=sc) - weibull.logsf(x, c, scale=sc)
    elif dist == 'gamma':
        logh = lambda x, a, sc: gamma.logpdf(x, a, scale=sc) - gamma.logsf(x, a, scale=sc)
    elif dist == 'lognorm':
        logh = lambda x, s, sc: lognorm.logpdf(x, s, scale=sc) - lognorm.logsf(x, s, scale=sc)
    else:
        raise ValueError("Invalid dist")
    return curve_fit(logh, xs, np.log(ys))

def fit(dist, xs, ys):
    """ returns a dictionary of parameters """
    if dist == 'weibull':
        h = lambda x, c, sc: weibull.pdf(x, c, scale=sc) / weibull.sf(x, c, scale=sc)
    elif dist == 'gamma':
        h = lambda x, a, sc: gamma.pdf(x, a, scale=sc) / gamma.sf(x, a, scale=sc)
    elif dist == 'lognorm':
        h = lambda x, s, sc: lognorm.pdf(x, s, scale=sc) / lognorm.sf(x, s, scale=sc)
    else:
        raise ValueError("Invalid dist")
    return curve_fit(h, xs, ys)

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
