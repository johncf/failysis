# Disk Failure Analysis

These are scripts used to generate failure rate curves from field data.

Example invocations of each script:

```sh
$ ./basic-plot.py -o plot.svg fails.csv obsct.csv
$ ./discrete-plot.py -o plot.svg fails.csv obsct.csv
$ ./dist-fit.py -o plot.svg --scale log fails.csv obsct.csv
$ ./dist-plot.py -o plot.svg # distribution parameters are hard-coded
```

In the above examples,

- `fails.csv` lists the cumulative number of failures with respect to power-on hours.
- `obsct.csv` lists the number of disks that were observed as a function of power-on hours.

## Helpful Resources

TODO
