# uowc/modulation.py
import numpy as np

def ber_ook_awgn(snr_linear: float) -> float:
    from math import erfc, sqrt
    return 0.5 * erfc(np.sqrt(snr_linear/2.0))

def ber_ppm_awgn(M: int, snr_per_symbol: float) -> float:
    """
    Placeholder closed-form for coherent PPM is different; 
    under IM/DD with AWGN, derive appropriately or estimate by Monte Carlo later.
    For now, keep a stub to wire pipeline; replace with validated formula/sim.
    """
    return max(1e-9, 0.5*np.exp(-snr_per_symbol/(2*np.log2(M)+1e-9)))
