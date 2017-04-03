#!/usr/bin/env python2
import os.path as path
from glob import glob
import numpy as np
import logging
import click
import tqdm
import scipy.misc as sm
import clustertools.db.tools as cdbt
from clustertools.log import LOGFORMAT


LOGGER = logging.getLogger(__name__)


@click.command()
@click.argument("in_fp", type=click.Path(exists=True, readable=True,
                                         file_okay=False))
@click.option("--out_fp", type=click.Path(), default=None,
              help=("Output db name. If unspecified, uses "
                    "`{in_fp}_p{x}.tfrecords` for the parts."))
@click.option("--examples_per_file", type=click.INT, default=1000,
              help="Number of examples per .tfrecord part.")
@click.option("--num_threads", type=click.INT, default=4,
              help="Number of threads to use for loading and encoding.")
def cli(in_fp, out_fp=None, examples_per_file=1000, num_threads=4):
    global load_fp, colendings,  colfullnames, fillwidth
    load_fp = in_fp
    if out_fp is None:
        out_fp = in_fp
    LOGGER.info("Packing contents of `%s` into db `%s`.", in_fp, out_fp)
    for fillwidth in range(1, 9):
        zero_entries = glob(path.join(in_fp, "{0:0{width}}_*.*".format(
            0, width=fillwidth)))
        if len(zero_entries) > 0:
            break
    colnames, colfullnames, colendings, coltypes = [], [], [], []
    LOGGER.info("Columns:")
    for fp in zero_entries:
        fn = path.basename(fp)
        if len(fn.split(".")) > 2:
            raise Exception("No dots apart from file-ending allowed!")
        colt = None
        colfulln = fn[fn.find("_")+1:fn.find(".")]
        if ":" in colfulln:
            coln = colfulln[:colfulln.find(":")]
            colt = colfulln[colfulln.find(":")+1:]
            assert colt in ['jpg', 'jpeg', 'png', 'webp'], (
                "':' only allowed in colname as image storage spec in "
                "[jpg, jpeg, png, webp] (is `%s`)!" % (colt))
        else:
            coln = colfulln
        fending = fn[fn.find(".")+1:]
        if colt is None:
            if fending in ['jpg', 'jpeg', 'png', 'webp']:
                colt = fending
            elif fending == 'txt':
                colt = 'text'
            elif fending == 'npy':
                colt = 'plain'
        LOGGER.info("  %s: %s", colfulln, colt)
        colnames.append(coln)
        colfullnames.append(colfulln)
        coltypes.append(colt)
        colendings.append(fending)
    LOGGER.info("Scanning...")
    nsamples = 0
    scan_complete = False
    pbar = tqdm.tqdm()
    while not scan_complete:
        for coln, colt, cole in zip(colfullnames, coltypes, colendings):
            if not path.exists(path.join(in_fp, "{0:0{width}}_{1}.{2}".format(
                    nsamples, coln, cole, width=fillwidth))):
                scan_complete = True
                break
        if scan_complete:
            break
        nsamples += 1
        pbar.update(1)
    pbar.close()
    LOGGER.info("%d complete examples located.", nsamples)
    LOGGER.info("Creating database...")
    colspec = []
    for coln, colt in zip(colnames, coltypes):
        if colt == 'text':
            colspec.append((coln, cdbt.SPECTYPES.text))
        elif colt == 'plain':
            colspec.append((coln, cdbt.SPECTYPES.implain))
        elif colt in ['jpg', 'jpeg']:
            colspec.append((coln, cdbt.SPECTYPES.imlossy))
        elif colt in ['png', 'webp']:
            colspec.append((coln, cdbt.SPECTYPES.imlossless))
        else:
            raise Exception("Unknown coltype (%s)!" % (colt))
    creator = cdbt.TFRecordCreator(colspec)
    creator.open(out_fp, examples_per_file=examples_per_file)
    creator.add_to_dset(
        file_loader,
        range(nsamples),
        num_threads=num_threads,
        progress=True
    )
    creator.close()
    LOGGER.info("Done.")


load_fp = None
colendings = None
colfullnames = None
fillwidth = None


def file_loader(sample_idx):
    results = []
    for coln, cole in zip(colfullnames, colendings):
        val = None
        fp = path.join(load_fp, '{0:0{width}}_{1}.{2}'.format(
            sample_idx, coln, cole, width=fillwidth))
        if cole == 'txt':
            val = ''
            with open(fp, 'r') as inf:
                for line in inf:
                    val += line
        elif cole == 'npy':
            val = np.load(fp)
        elif cole in ['png', 'jpg', 'jpeg', 'webp']:
            val = sm.imread(fp)
        results.append(val)
    return [results]


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOGFORMAT)
    cli()
