# Disk Failure Analysis

These are scripts used to generate failure rate curves from field data.

Example invocations of each script is as follows:
```sh
$ ./basic-plot.py -o plot.svg cumu-fails.csv obs-pop.csv
$ ./discrete-plot.py -o plot.svg cumu-fails.csv obs-pop.csv
$ ./dist-fit.py -o plot.svg --scale log cumu-fails.csv obs-pop.csv
$ ./dist-plot.py -o plot.svg # distribution parameters are hard-coded
$ ./multi-plot.py -o plot.svg long.json
```

In the above examples,

- `cumu-fails.csv` is the file which contains the cumulative number of failures
  in the entire system (or the set of disks we are observing) along with the
  age (in power-on hours) at which each one failed.
- `obs-pop.csv` is the number of disks under observation at various points in
  the age domain. That is, the count of disks that were observed at various
  points of age (in power-on hours).
- `long.json` is a json file describing the locations of these data files for
  various populations. An example is included in this repository.

SQL queries for generating `cumu-fails` and `obs-pop` with various filters from
disk activity and failure logs are provided in the [`sql`](./sql) directory.
