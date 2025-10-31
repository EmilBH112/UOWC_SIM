"""
Link-level modeling for an underwater optical wireless link.

This module wires together: water attenuation (Beer–Lambert), source/receiver
geometry (LED/Lambertian vs laser-like narrow beam), turbulence fading, and a
current-domain noise model to produce SNR and feed BER calculators.

Key assumptions and simplifications:
- Single wavelength scalar model (use WaterType presets at ~520 nm).
- Line-of-sight link; scattering treated implicitly via c = a + b (Beer–Lambert).
- Ideal non-imaging concentrator with gain ~ n^2 / sin^2(FOV) and hard FOV cutoff.
- Turbulence modeled as unit-mean multiplicative fading (log-normal / GG / Weibull).
- Electrical noise combined in current domain; signal current = R * Pr.

You can refine this by adding background light, APD gain/excess noise, and full
angular radiance models; hooks are marked below.
"""

from dataclasses import dataclass
import numpy as np
from .media import WaterType

# Physical constants
q = 1.602e-19           # electron charge [C]
kB = 1.380649e-23       # Boltzmann constant [J/K]


# ----------------------
# Transmitter / Receiver
# ----------------------
@dataclass
class Tx:
    """Optical transmitter description.

    Pt_w: launched optical power [W] at the transmitter output.
    eta_t: transmitter optics efficiency (0..1).
    semi_angle_deg: LED semi-angle at half power (Lambertian).
    is_laser: if True, use a narrow-beam geometric model.
    theta_div_deg: approximate divergence half-angle for laser-like source.
    m_lambert: optional override for Lambertian order m.
    """

    Pt_w: float
    eta_t: float = 0.9
    semi_angle_deg: float = 60
    is_laser: bool = False
    theta_div_deg: float = 9.0
    m_lambert: float | None = None

    def lambert_m(self) -> float:
        """Return the Lambertian order m from the semi-angle definition.
        m = -ln(2) / ln(cos(theta_1/2))
        """
        if self.is_laser:
            return 1.0  # unused for laser branch
        if self.m_lambert is not None:
            return self.m_lambert
        th = np.deg2rad(self.semi_angle_deg)
        return -np.log(2.0) / np.log(np.cos(th))


@dataclass
class Rx:
    """Optical receiver and front-end knobs.

    R_A_per_W: photodetector responsivity [A/W] at the chosen wavelength.
    A_pd_m2: active area of the detector [m^2].
    eta_r: receive optics/filter efficiency (0..1).
    T: front-end temperature [K] for thermal noise.
    R_load: effective transimpedance / load for thermal noise model [Ohm].
    """

    R_A_per_W: float
    A_pd_m2: float
    eta_r: float = 0.9
    T: float = 300.0
    R_load: float = 50.0


# ---------
# Geometry
# ---------
@dataclass
class Geometry:
    """Geometric arrangement and simple optics.

    distance_m: Tx–Rx separation [m].
    theta_tx_deg: beam divergence half-angle (LED) or used as geometry param.
    phi_incident_deg: incidence angle at the receiver relative to normal [deg].
    fov_deg: receiver acceptance half-angle [deg].
    G_tx_optics: optional transmitter optics gain (e.g., expander).
    n_concentrator: refractive index of the concentrator.
    """

    distance_m: float
    theta_tx_deg: float
    phi_incident_deg: float
    fov_deg: float
    G_tx_optics: float = 1.0
    n_concentrator: float = 1.5

    def rx_concentrator_gain(self) -> float:
        """Idealized non-imaging concentrator gain ~ n^2 / sin^2(FOV).
        Narrower FOV => larger gain. Guard against divide-by-zero at tiny FOV.
        """
        phi = np.deg2rad(self.fov_deg)
        s = np.sin(phi)
        return (self.n_concentrator**2) / max(s*s, 1e-12)

    def fov_window(self, phi_incident_deg: float) -> float:
        """Hard cutoff: pass only if incidence is within FOV."""
        return 1.0 if abs(phi_incident_deg) <= self.fov_deg else 0.0


# -----------
# Turbulence
# -----------
@dataclass
class Turbulence:
    """Multiplicative fading models with unit-mean normalization.

    model_name: 'lognormal' | 'gen-gamma' | 'weibull'
    scint_index: sigma_I^2 (scintillation index). If 0 => deterministic.
    Other params control tail shape for GG/Weibull placeholders.
    """

    model_name: str = 'lognormal'
    scint_index: float = 0.0
    gg_alpha: float = 1.0
    gg_beta: float = 1.0
    weibull_k: float = 1.0
    weibull_lambda: float = 1.0

    @staticmethod
    def model(name: str, **kwargs):
        return Turbulence(model_name=name, **kwargs)

    def fading_gain(self, size=1):
        """Draw fading gains with E[g]=1.
        - Log-normal: set log-amplitude mean so intensity is unit-mean.
        - GG/Weibull: sample then normalize by sample mean.
        """
        if self.scint_index <= 0:
            return np.ones(size)
        name = self.model_name.lower()
        if name == 'lognormal':
            # σ_X^2 = ln(1+σ_I^2) with μ = -σ_X^2/2 for unit-mean intensity
            sigmaX2 = np.log(1.0 + self.scint_index)
            mu = -0.5 * sigmaX2
            return np.exp(np.random.normal(mu, np.sqrt(sigmaX2), size=size))
        if name in ('gen-gamma', 'generalized-gamma'):
            g = np.random.gamma(shape=self.gg_beta, scale=self.gg_alpha, size=size)
            return g / np.mean(g)
        if name == 'weibull':
            g = np.random.weibull(a=self.weibull_k, size=size) * self.weibull_lambda
            return g / np.mean(g)
        return np.ones(size)


# ----
# Link
# ----
class Link:
    """Compute received power and SNR for a given setup."""

    def __init__(self, water: WaterType, tx: Tx, rx: Rx, geom: Geometry, turb: Turbulence):
        self.water = water
        self.tx = tx
        self.rx = rx
        self.geom = geom
        self.turb = turb

    # Geometry factors (simplified LED vs LD).
    # For LED we use a Lambertian-like form; for LD we approximate a narrow cone.
    def _geom_gain_led(self) -> float:
        m = self.tx.lambert_m()
        theta = np.deg2rad(self.geom.theta_tx_deg)
        G_tx = self.geom.G_tx_optics
        G_rx = self.geom.rx_concentrator_gain()
        phi = self.geom.phi_incident_deg
        Pi = self.geom.fov_window(phi)
        d = self.geom.distance_m

        # NOTE: This is a simplified geometry. A common VLC LOS form is:
        # H = ((m+1) A_r / (2π d^2)) cos^m(theta) * T_s(φ) * g(φ) * cos(φ), φ <= ψ_c
        # Here we fold T_s into eta_r and use G_tx_optics, and enforce a hard FOV window.
        denom = 2 * np.pi * d * d
        cos_phi = max(np.cos(np.deg2rad(phi)), 0.0)
        num = ((m + 1) / (2 * np.pi)) * (np.cos(theta) ** m) * G_tx * G_rx * self.rx.A_pd_m2 * cos_phi
        return Pi * max(num / max(denom, 1e-24), 0.0)

    def _geom_gain_ld(self) -> float:
        # Treat as a narrow divergence cone with area growth ~ π d^2 tan^2(theta).
        theta = np.deg2rad(max(self.tx.theta_div_deg, 0.5))
        G_tx = self.geom.G_tx_optics
        G_rx = self.geom.rx_concentrator_gain()
        phi = self.geom.phi_incident_deg
        Pi = self.geom.fov_window(phi)
        d = self.geom.distance_m
        denom = np.pi * d * d * (np.tan(theta) ** 2 + 1e-12)
        cos_phi = max(np.cos(np.deg2rad(phi)), 0.0)
        num = G_tx * G_rx * self.rx.A_pd_m2 * cos_phi
        return Pi * max(num / denom, 0.0)

    def received_power_W(self, stochastic: bool = False) -> float:
        """Deterministic (or faded) received power at the PD input [W].

        Pr = Pt * eta_t * exp(-c d) * G_geom * eta_r * g_turb
        """
        Pt = self.tx.Pt_w * self.tx.eta_t
        c = self.water.c_m1
        atten = np.exp(-c * self.geom.distance_m)
        G = self._geom_gain_ld() if self.tx.is_laser else self._geom_gain_led()
        turb = 1.0
        if stochastic and self.turb.scint_index > 0:
            turb = float(self.turb.fading_gain(size=1)[0])
        return Pt * atten * G * self.rx.eta_r * turb

    def noise_variances(self, Pr_W: float, bandwidth_Hz: float, rin: float | None, Idark_A: float,
                         Pbg_W: float = 0.0, R_apd_M: float = 1.0, F_excess: float = 1.0) -> dict:
        """Return individual noise variances in current domain.

        - Shot: 2 q R (Pr + Pbg) B * F_excess (APD excess if used)
        - Thermal: 4 k T B / R_L
        - Dark: 2 q I_dark B
        - RIN: (R·Pr)^2 B · rin
        """
        R = self.rx.R_A_per_W * R_apd_M
        B = bandwidth_Hz
        shot = 2 * q * R * (Pr_W + Pbg_W) * B * F_excess
        thermal = 4 * kB * self.rx.T * B / max(self.rx.R_load, 1e-3)
        dark = 2 * q * Idark_A * B if Idark_A and Idark_A > 0 else 0.0
        rin_var = (R * Pr_W) ** 2 * B * rin if rin is not None else 0.0
        return dict(shot=shot, thermal=thermal, dark=dark, rin=rin_var)

    def snr_db(self, bandwidth_Hz: float, rin: float | None = None, Idark_A: float = 0.0,
               Pbg_W: float = 0.0, R_apd_M: float = 1.0, F_excess: float = 1.0) -> float:
        """Electrical SNR (dB) computed as (signal current)^2 / total noise variance."""
        Pr = self.received_power_W()
        R = self.rx.R_A_per_W * R_apd_M
        sig = (R * Pr) ** 2
        nv = self.noise_variances(Pr, bandwidth_Hz, rin, Idark_A, Pbg_W=Pbg_W, R_apd_M=R_apd_M, F_excess=F_excess)
        sigma2 = sum(nv.values())
        snr = sig / max(sigma2, 1e-30)
        return 10 * np.log10(snr + 1e-30)
