#!env python3

from scipy.stats import weibull_min as weibull, gamma, lognorm
import matplotlib.pyplot as plt
import numpy as np

def main(xmin=0, xmax=16, outfile='/tmp/plot.svg', scale='normal'):
    dist_pars = [['weibull', 2.84, 8.56],
                 ['gamma', 4.78, 1.75],
                 ['lognorm', 0.528, np.exp(2.0835)]]

    fig, ax = plt.subplots()
    fig.set_size_inches(5.3, 3)

    ax.set_xlabel("Power-on years")
    ax.set_ylabel("PDF")
    if scale == 'log':
        ax.set_yscale("log")
    #    ax.set_ylim(2e-1, 100)
    #else:
    #    ax.set_ylim(0, 30)

    xs = np.linspace(xmin, xmax, 2000)
    for dist, p1, p2 in dist_pars:
        ys = gen_ys(dist, [p1, p2], xs)
        ax.plot(xs, ys, label=dist)

    ax.legend()
    fig.savefig(outfile, bbox_inches="tight")

def gen_ys(dist, params, xs):
    """ returns ys corresponding to xs """
    p1 = params[0]
    sc = params[1]
    if dist == 'weibull':
        f = lambda x: weibull.pdf(x, p1, scale=sc)
    elif dist == 'gamma':
        f = lambda x: gamma.pdf(x, p1, scale=sc)
    elif dist == 'lognorm':
        f = lambda x: lognorm.pdf(x, p1, scale=sc)
    else:
        raise ValueError("Invalid dist")
    return np.vectorize(f)(xs)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute failure rate distribution over '
                        'power-on hours, given the cumulative failures '
                        'and observed population over it.')
    parser.add_argument('-o', metavar='FILE', default='/tmp/plot.svg',
                        help='output failure rate plots to %(metavar)s')
    parser.add_argument('--xmin', metavar='XMIN', default='0')
    parser.add_argument('--xmax', metavar='XMAX', default='7')
    parser.add_argument('--scale', metavar='TYPE', default='normal',
                        help='scale used when fitting (choices: normal, log)')
    args = parser.parse_args()
    main(outfile=args.o, scale=args.scale)
