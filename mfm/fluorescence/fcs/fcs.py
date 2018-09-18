from mfm.fluorescence.fcs import _fcs
import numpy as np
from math import floor, pow
import numba as nb

weightCalculations = ['Koppel', 'none']
correlationMethods = ['tp']


def normalize(np1, np2, dt1, dt2, tau, corr, B):
    cr1 = float(np1) / float(dt1)
    cr2 = float(np2) / float(dt2)
    for j in range(corr.shape[0]):
        pw = 2.0 ** int(j / B)
        tCor = dt1 if dt1 < dt2 - tau[j] else dt2 - tau[j]
        corr[j] /= (tCor * float(pw))
        corr[j] /= (cr1 * cr2)
        tau[j] = tau[j] // pw * pw
    return float(min(cr1, cr2))


@nb.jit
def get_weights(rout, tac, wt, nPh):
    w = np.zeros(nPh, dtype=np.float32)
    for i in range(nPh):
        w[i] = wt[rout[i], tac[i]]
    return w


@nb.jit
def count_rate_filter(mt, tw, n_ph_max, w, n_ph):
    i = 0
    while i < n_ph - 1:
        r = i
        i_ph = 0
        while (mt[r] - mt[i]) < tw and r < n_ph - 1:
            r += 1
            i_ph += 1
        if i_ph > n_ph_max:
            for k in range(i, r):
                w[k] = 0
        i = r


@nb.jit(nopython=True)
def make_fine(t, tac, nTAC):
    for i in range(1, t.shape[0]):
        t[i] = t[i] * nTAC + tac[i]


@nb.jit
def count_photons(w):
    k = np.zeros(w.shape[0], dtype=np.uint64)
    for j in range(w.shape[0]):
        for i in range(w.shape[1]):
            if w[j, i] != 0.0:
                k[j] += 1
    return k


@nb.jit(nopython=True)
def compact(t, w, full=0):
    for j in range(t.shape[0]):
        k = 1
        r = t.shape[1] if full else t[j, 0]
        for i in range(1, r):
            if t[j, k] != t[j, i] and w[j, i] != 0:
                k += 1
                t[j, k] = t[j, i]
                w[j, k] = w[j, i]
        t[j, 0] = k - 1


@nb.jit(nopython=True)
def coarsen(t, w):
    for j in range(t.shape[0]):
        t[j, 1] /= 2
        for i in range(2, t[j, 0]):
            t[j, i] /= 2
            if t[j, i - 1] == t[j, i]:
                w[j, i - 1] += w[j, i]
                w[j, i] = 0.0
    compact(t, w, 0)


def calc_lifetime_filter(decays, experimental_decay, normalize_patterns=True):
    """Calculates filters for lifetime filtered correlations according to Enderlein

    :param decays: a list of fluorescence decays
    :param experimental_decay: the experimental fluorescence decay
    :return: an array of the filters

    Examples
    --------

    >>> lifetime_1 = 1.0
    >>> lifetime_2 = 3.0
    >>> t = np.linspace(0, 20, num=10)
    >>> d1 = np.exp(-t/lifetime_1)
    >>> d2 = np.exp(-t/lifetime_2)
    >>> decays = [d1, d2]
    >>> w1 = 0.8  # weight of first component
    >>> experimental_decay = w1 * d1 + (1.0 - w1) * d2
    >>> filters = calc_lifetime_filter(decays, experimental_decay)
    >>> calc_lifetime_filter(decays, experimental_decay)
    array([[ 1.19397553, -0.42328685, -1.94651679, -2.57788423, -2.74922322,
            -2.78989942, -2.79923872, -2.80136643, -2.80185031, -2.80196031],
           [-0.19397553,  1.42328685,  2.94651679,  3.57788423,  3.74922322,
             3.78989942,  3.79923872,  3.80136643,  3.80185031,  3.80196031]])


    Using a structure to generate lifetime filters

    >>> import mfm
    >>> from mfm.fluorescence.general import calculate_fluorescence_decay
    >>> import numpy as np

    >>> time_axis = np.linspace(0, 10, num=100)
    >>> structure = mfm.structure.Structure('./sample_data/modelling/pdb_files/hGBP1_closed.pdb')
    >>> donor_description = {'residue_seq_number': 344, 'atom_name': 'CB'}
    >>> acceptor_description = {'residue_seq_number': 496, 'atom_name': 'CB'}
    >>> donor_lifetime_spectrum = np.array([1., 4.])
    >>> lifetime_spectrum = structure.av_lifetime_spectrum(donor_lifetime_spectrum, donor_description, acceptor_description)
    >>> t, decay_1 = calculate_fluorescence_decay(lifetime_spectrum, time_axis)

    >>> donor_description = {'residue_seq_number': 18, 'atom_name': 'CB'}
    >>> acceptor_description = {'residue_seq_number': 577, 'atom_name': 'CB'}
    >>> donor_lifetime_spectrum = np.array([1., 4.])
    >>> lifetime_spectrum = structure.av_lifetime_spectrum(donor_lifetime_spectrum, donor_description, acceptor_description)
    >>> t, decay_2 = calculate_fluorescence_decay(lifetime_spectrum, time_axis)

    >>> fraction_1 = 0.1
    >>> experimental_decay = fraction_1 * decay_1 + (1. - fraction_1) * decay_2
    >>> decays = [decay_1, decay_2]
    >>> filters = calc_lifetime_filter(decays, experimental_decay, normalize_patterns=False)

    >>> a0 = np.dot(filters[0], experimental_decay)
    >>> a1 = np.dot(filters[1], experimental_decay)

    References
    ----------

    .. [1] Fluorescence Lifetime Correlation Spectroscopy, Peter Kapusta,
       Michael Wahl, Ales Benda, Martin Hof, Jorg Enderlein,
       Journal of Fluorescence, 2007, 17:43-48
    .. [2] Fast fitting of multi-exponential decay curves, Jorg Enderlein,
       Rainer Erdmann, 1997, 134, 371-378, Optics Communications
    .. [3] Time-resolved fluorescence correlation spectroscopy
       Martin Bohmer, Michaek Wahl, Hans-Jurgen Rahn, Rainer Erdmann, Jorg Enderlein,
       Chemical Physics Letters 353 (2002), 439-445
    """
    # normalize the fluorescence decays which serve as reference
    if normalize_patterns:
        decay_patterns = [decay / decay.sum() for decay in decays]
    else:
        decay_patterns = decays
    d = np.diag(1. / experimental_decay)
    m = np.stack(decay_patterns)
    iv = np.linalg.pinv(np.dot(m, np.dot(d, m.T)))
    r = np.dot(np.dot(iv, m), d)
    if normalize_patterns:
        w = np.array([np.dot(fi, experimental_decay) for fi in r]).sum()
        r /= w
    return r


def log_corr(mt, tac, rout, cr_filter, w1, w2, B, nc, fine, nTAC):
    """Correlate macro-times and micro-times using a logarit

    :param mt: the macro-time array
    :param tac: the micro-time array
    :param rout: the array of routing channels
    :param cr_filter:
    :param w1:
    :param w2:
    :param B:
    :param nc:
    :param fine:
    :param nTAC:
    :return:
    """

    # correlate with TAC
    if fine > 0:
        make_fine(mt, tac, nTAC)
    # make 2 corr-channels
    t = np.vstack([mt, mt])
    w = np.vstack([w1 * cr_filter, w2 * cr_filter])
    np1, np2 = count_photons(w)
    compact(t, w, 1)
    # MACRO-Times
    mt1max, mt2max = t[0, t[0, 0]], t[1, t[1, 0]]
    mt1min, mt2min = t[0, 1], t[1, 1]
    dt1 = mt1max - mt1min
    dt2 = mt2max - mt2min
    # calculate tau axis
    taus = np.zeros(nc * B, dtype=np.uint64)
    corr = np.zeros(nc * B, dtype=np.float32)
    for j in range(1, nc * B):
        taus[j] = taus[j - 1] + pow(2.0, floor(j / B))
    # correlation
    for n in range(nc):
        print "cascade %s\tnph1: %s\tnph2: %s" % (n, t[0,0], t[1,0])
        _fcs.correlate(n, B, t, taus, corr, w)
        coarsen(t, w)
    return np1, np2, dt1, dt2, taus, corr


