#!/usr/bin/env python

"""Make a plot to verify the rate of false alarms from PyCBC Live."""

import argparse
import glob
import h5py
import tqdm
import lal
import numpy as np
import matplotlib
matplotlib.use('agg')
import pylab as pl
from scipy.stats import poisson


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-files', required=True)
parser.add_argument('--output-plot', required=True)
args = parser.parse_args()

ifars = []
stats = []
upload_thresholds = set()
pvalue_livetimes = set()
dfuts = set()
time = 0.

for fn in tqdm.tqdm(glob.glob(args.input_files)):
    with h5py.File(fn, 'r') as f:
        if 'num_live_detectors' not in f.attrs:
            continue
        if f.attrs['num_live_detectors'] > 1:
            time += 8
        try:
            ifar = f['foreground/ifar'][()]
            stat = f['foreground/stat'][0]
        except KeyError:
            continue
        #if 'foreground/NO_FOLLOWUP' in f:
        #    continue
        ifars.append(ifar)
        stats.append(stat)

        cl = f.attrs['command_line']
        for i, arg in enumerate(cl):
            if i == 0:
                continue
            if cl[i-1] == '--ifar-upload-threshold':
                upload_thresholds.add(float(arg))
            elif cl[i-1] == '--pvalue-combination-livetime':
                pvalue_livetimes.add(float(arg))
            elif cl[i-1] == '--ifar-double-followup-threshold':
                dfuts.add(float(arg))

ifars = np.sort(np.array(ifars))
count = np.arange(len(ifars))[::-1] + 1
time = time / lal.YRJUL_SI
rate = count / time

pl.step(ifars, rate, label='Observation')

ifars2 = np.logspace(np.log10(ifars.min()), np.log10(ifars.max()), 1000)
label = 'Expectation'
for prob in [0.6827, 0.9545, 0.9973]:
    a, b = poisson.interval(prob, time / ifars2)
    pl.fill_between(ifars2, a / time,
                    b / time, alpha=0.3,
                    edgecolor='none', facecolor='C1', label=label)
    label = None

for ut in upload_thresholds:
    pl.axvline(ut, color='r', ls='--', label='--ifar-upload-threshold')

for pvlt in pvalue_livetimes:
    pl.axvline(pvlt, color='b', ls=':', label='--pvalue-combination-livetime')

for dfut in dfuts:
    pl.axvline(dfut, color='g', ls='-.',
               label='--ifar-double-followup-threshold')

pl.xscale('log')
pl.yscale('log')
pl.xlabel('Inverse FAR [yr]')
pl.ylabel('Cumulative rate [yr$^{-1}$]')
pl.title(args.input_files, fontsize=10)
pl.legend(fontsize=10)

pl.tight_layout()
pl.savefig(args.output_plot, dpi=200)
