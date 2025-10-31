import numpy as np
from math import erfc, sqrt

def qfunc(x: float) -> float:
    return 0.5 * erfc(x / sqrt(2))

def ber_ook_from_snr_db(snr_db: float) -> float:
    snr_lin = 10**(snr_db/10)
    return float(qfunc(np.sqrt(snr_lin)))

def ppm_encode(bits, M: int):
    import numpy as np
    bits = np.asarray(bits).astype(int) & 1
    k = int(np.ceil(np.log2(M)))
    pad = (-len(bits)) % k
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=int)])
    syms = bits.reshape(-1, k)
    idx = np.packbits(syms[:, ::-1], bitorder='little', axis=1)[:,0] % M
    out = np.zeros((len(idx), M), dtype=int)
    out[np.arange(len(idx)), idx] = 1
    return out
