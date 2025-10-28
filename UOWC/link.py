# uowc/link.py
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from typing import Literal, Optional
from .media import WaterMedium

TurbulenceModel = Literal["lognormal", "gen-gamma", "weibull"]

@dataclass
class Transmitter:
    power_w: float             # optical power at source [W]
    tx_optical_eff: float = 1.0  # optics efficiency (0..1)
    divergence_half_angle_rad: float = math.radians(5)  # not used yet in LOS

@dataclass
class Receiver:
    aperture_area_m2: float    # physical area [m^2]
    rx_optical_eff: float = 1.0  # optics/filter efficiency (0..1)
    fov_half_angle_rad: float = math.radians(10)        # placeholder

@dataclass
class Channel:
    wavelength_nm: float
    medium: WaterMedium
    turbulence: TurbulenceModel = "lognormal"
    sigma_ln: float = 0.2
    """
    sigma_ln: log-amplitude std dev for log-normal fading (weak-to-mod turbulence).
    You can later switch to generalized-gamma / Weibull with their params as in Zayed & Shokair.
    """

    def los_power(self, tx: Transmitter, rx: Receiver, distance_m: float) -> float:
        """
        Simple LOS received power:
            P_r_LOS = P_t * η_tx * η_rx * (A_r / (4π d^2)) * exp(-c d)
        where c = a + b. Matches common UOWC LOS modeling used in Scientific Reports work. 
        """
        spreading = rx.aperture_area_m2 / (4.0 * math.pi * distance_m**2)
        beer_lambert = math.exp(-self.medium.c * distance_m)
        return tx.power_w * tx.tx_optical_eff * rx.rx_optical_eff * spreading * beer_lambert

    # ---- Turbulence fading samples (intensity multiplier) ----
    def fading_samples(self, n: int) -> np.ndarray:
        """
        Draw i.i.d. samples of turbulence-induced intensity fading.
        Start with log-normal for weak/moderate regimes; add others later.
        References discuss log-normal (weak), generalized-gamma, Weibull (moderate/strong). 
        """
        if self.turbulence == "lognormal":
            # Intensity I = I0 * exp(X), X ~ N(-σ^2/2, σ^2) to keep E[I]=I0
            mu = -0.5 * self.sigma_ln**2
            return np.exp(np.random.normal(mu, self.sigma_ln, size=n))
        elif self.turbulence == "weibull":
            # Placeholder Weibull(k, λ) with mean 1 (normalize)
            k, lam = 1.5, 1.0
            samp = np.random.weibull(k, size=n) * lam
            return samp / np.mean(samp)
        elif self.turbulence == "gen-gamma":
            # Placeholder generalized-gamma; normalize to mean 1
            # shape a,k and scale d — tune from literature once you pick regime.
            a, d, p = 2.0, 1.0, 1.0
            x = np.random.gamma(shape=a, scale=d, size=n)**(1.0/p)
            return x / np.mean(x)
        else:
            raise ValueError("Unknown turbulence model")

    def received_power_samples(self, tx: Transmitter, rx: Receiver, distance_m: float, n: int = 10000) -> np.ndarray:
        """
        Monte-Carlo of received power with multiplicative turbulence.
        """
        pr_los = self.los_power(tx, rx, distance_m)
        fade = self.fading_samples(n)
        return pr_los * fade

    # ---- SNR/BER (1st-order placeholders) ----
    def snr_imdd_awgn(self, pr_w: float, noise_psd_a2_hz: float = 1e-24, responsivity_a_w: float = 0.2, bandwidth_hz: float = 1e5) -> float:
        """
        Very simple IM/DD SNR estimate:
            signal current ~ R * P_r
            noise current variance ~ N0 * B   (placeholder single-sided PSD)
        Extend with shot noise, thermal noise, APD gain/excess noise later.
        """
        i_sig = responsivity_a_w * pr_w
        var = noise_psd_a2_hz * bandwidth_hz
        return (i_sig**2) / (var + 1e-30)

    def ber_ook_awgn(self, snr_linear: float) -> float:
        """
        OOK with optimal threshold in AWGN (equal priors):
            BER ≈ Q( sqrt(SNR) )
        """
        from math import erfc, sqrt
        return 0.5 * erfc( math.sqrt(snr_linear)/math.sqrt(2.0) )

    
