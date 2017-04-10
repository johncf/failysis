#!/bin/python

outfile = 'plot.svg'

def stepify(xs, ys):
    last_y = ys[0]
    res_xs = [xs[0]]
    res_ys = [ys[0]]
    for (x, y) in zip(xs[1:], ys[1:]):
        res_xs.append(x)
        res_ys.append(last_y)
        res_xs.append(x)
        res_ys.append(y)
        last_y = y
    return res_xs, res_ys

def main():
    import matplotlib.pyplot as plt
    fig, axh = plt.subplots(1, 1)
    fig.set_size_inches(3.5, 2.3)

    axh.set_ylabel("# disks under observation")
    axh.set_xlabel("Power-on hours")
    axh.set_ylim(0, 4)
    #axh.set_xlim(-2e3, 62e3)
    xs = [ 0, 100, 700, 2400, 2900, 3400, 4000, 4500, 5600 ]
    ys = [ 0,   1,   0,    1,    2,    1,    2,    1,    0 ]
    xs, ys = stepify(xs, ys)
    axh.fill_between(xs, ys, color='#0766aa33')

    #fig.tight_layout()
    fig.savefig(outfile, bbox_inches="tight")
    print("Written failure rate plot to", outfile)

if __name__ == '__main__':
    main()
