# examples/quickstart.py
from uowc.media import PURE_SEA, CLEAR_COASTAL, TURBID_HARBOR
from uowc.link import Transmitter, Receiver, Channel
import numpy as np

# --- Define system ---
tx = Transmitter(power_w=0.03, tx_optical_eff=0.8)        # 30 mW LED, 80% optics
rx = Receiver(aperture_area_m2=5e-4, rx_optical_eff=0.7)  # ~25 mm dia lens => A≈4.9e-4 m^2
ch = Channel(wavelength_nm=520.0, medium=CLEAR_COASTAL, turbulence="lognormal", sigma_ln=0.25)

# --- Single-distance sanity check ---
d = 2.0  # meters
pr = ch.los_power(tx, rx, d)
print(f"LOS received power at {d:.1f} m: {pr*1e9:.2f} nW")

# --- Monte-Carlo with turbulence ---
samples = ch.received_power_samples(tx, rx, d, n=20000)
print(f"Turbulent mean: {samples.mean()*1e9:.2f} nW, scintillation (σ/I): {samples.std()/samples.mean():.3f}")

# --- Crude SNR/BER (IM/DD AWGN placeholder) ---
snr = ch.snr_imdd_awgn(pr_w=samples.mean(), noise_psd_a2_hz=5e-24, responsivity_a_w=0.2, bandwidth_hz=1e5)
from uowc.modulation import ber_ook_awgn
print(f"SNR (linear): {snr:.2f}, BER_OOK≈ {ber_ook_awgn(snr):.3e}")
