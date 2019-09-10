from __future__ import print_function, division, absolute_import

import bz2
import gzip
import io
import os
import zipfile

from mdtraj.utils.six import PY2, StringIO


def open_maybe_zipped(filename, mode, force_overwrite=True):
    # TODO: make it work with numpy and gzip files
    """Open a file in name (not binary) mode, transparently handling
    .gz or .bz2 compresssion, with utf-8 encoding.

    Parameters
    ----------
    filename : str
        Path to file. Compression will be automatically detected if
        the filename ends in .gz or .bz2.
    mode : {'r', 'w'}
        Mode in which to open file
    force_overwrite : bool, default=True
        If 'w', should we overwrite the file if something with `filename`
        already exists?

    Returns
    -------
    handle : file
        Open file handle.
    """
    _, extension = os.path.splitext(filename.lower())
    if mode == 'r':
        if extension == '.gz':
            with gzip.GzipFile(filename, 'r') as gz_f:
                #return StringIO(gz_f.read().decode('utf-8'))
                return gz_f
        elif extension == '.bz2':
            with bz2.BZ2File(filename, 'r') as bz2_f:
                return StringIO(bz2_f.read().decode('utf-8'))
                #return bz2_f
        elif extension == '.zip':
            with zipfile.ZipFile(filename, 'r') as zip_f:
                return StringIO(zip_f.read().decode('utf-8'))
                #return zip_f
        else:
            return open(filename, 'r')
    elif mode == 'w':
        if os.path.exists(filename) and not force_overwrite:
            raise IOError('"%s" already exists' % filename)
        if extension == '.gz':
            if PY2:
                return gzip.GzipFile(filename, 'w')
            binary_fh = gzip.GzipFile(filename, 'wb')
            return io.TextIOWrapper(binary_fh, encoding='utf-8')
        elif extension == '.bz2':
            if PY2:
                return bz2.BZ2File(filename, 'w')
            binary_fh = bz2.BZ2File(filename, 'wb')
            return io.TextIOWrapper(binary_fh, encoding='utf-8')
        elif extension == '.zip':
            if PY2:
                return zipfile.ZipFile(filename, 'w')
            binary_fh = zipfile.ZipFile(filename, 'wb')
            return io.TextIOWrapper(binary_fh, encoding='utf-8')
        else:
            return open(filename, 'w')
    else:
        raise ValueError('Invalid mode "%s"' % mode)
