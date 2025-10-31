"""
Basic modulation helpers for the simulator.

- OOK BER approximation (IM/DD with AWGN): BER ≈ Q(√SNR).
- Simple PPM encoder to create one-hot time-slot symbols from a bitstream.
"""
import numpy as np
from math import erfc, sqrt

def qfunc(x: float) -> float:
    return 0.5 * erfc(x / sqrt(2))

def ber_ook_from_snr_db(snr_db: float) -> float:
    """Return OOK BER from SNR in dB via Q(√SNR).
    This is a standard first-order approximation used in UOWC/VLC analyses.
    """
    snr_lin = 10**(snr_db/10)
    return float(qfunc(np.sqrt(snr_lin)))

def ppm_encode(bits, M: int):
    """Very simple M-PPM one-hot encoder (no framing/CRC).
    Packs ⌈log2 M⌉ bits per symbol and emits a one-hot row per symbol.
    """
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
