from dataclasses import dataclass
import numpy as np
from .media import WaterType

q = 1.602e-19
kB = 1.380649e-23

@dataclass
class Tx:
    Pt_w: float
    eta_t: float = 0.9
    semi_angle_deg: float = 60
    is_laser: bool = False
    theta_div_deg: float = 9.0
    m_lambert: float = None
    def lambert_m(self) -> float:
        if self.is_laser:
            return 1.0
        if self.m_lambert is not None:
            return self.m_lambert
        th = np.deg2rad(self.semi_angle_deg)
        return -np.log(2.0)/np.log(np.cos(th))

@dataclass
class Rx:
    R_A_per_W: float
    A_pd_m2: float
    eta_r: float = 0.9
    T: float = 300.0
    R_load: float = 50.0

@dataclass
class Geometry:
    distance_m: float
    theta_tx_deg: float
    phi_incident_deg: float
    fov_deg: float
    G_tx_optics: float = 1.0
    n_concentrator: float = 1.5
    def rx_concentrator_gain(self) -> float:
        phi = np.deg2rad(self.fov_deg)
        return (self.n_concentrator**2) * (np.sin(phi)**2)
    def fov_window(self, phi_incident_deg: float) -> float:
        return 1.0 if abs(phi_incident_deg) <= self.fov_deg else 0.0

@dataclass
class Turbulence:
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
        if self.scint_index <= 0:
            return np.ones(size)
        if self.model_name.lower() == 'lognormal':
            sigmaX2 = np.log(1.0 + self.scint_index)
            mu = -0.5*sigmaX2
            return np.exp(np.random.normal(mu, np.sqrt(sigmaX2), size=size))
        if self.model_name.lower() in ('gen-gamma','generalized-gamma'):
            g = np.random.gamma(shape=self.gg_beta, scale=self.gg_alpha, size=size)
            return g/np.mean(g)
        if self.model_name.lower() == 'weibull':
            g = np.random.weibull(a=self.weibull_k, size=size) * self.weibull_lambda
            return g/np.mean(g)
        return np.ones(size)

class Link:
    def __init__(self, water: WaterType, tx: Tx, rx: Rx, geom: Geometry, turb: Turbulence):
        self.water = water
        self.tx = tx
        self.rx = rx
        self.geom = geom
        self.turb = turb
    def _geom_gain_led(self) -> float:
        m = self.tx.lambert_m()
        theta = np.deg2rad(self.geom.theta_tx_deg)
        G_tx = self.geom.G_tx_optics
        G_rx = self.geom.rx_concentrator_gain()
        phi = self.geom.phi_incident_deg
        Pi = self.geom.fov_window(phi)
        d = self.geom.distance_m
        denom = 2*np.pi*d*d*(1 - np.cos(theta) + 1e-12)
        num = ((m+1)/(2*np.pi)) * (np.cos(theta)**m) * G_tx * G_rx * self.rx.A_pd_m2 * np.cos(np.deg2rad(phi))
        return Pi * max(num/denom, 0.0)
    def _geom_gain_ld(self) -> float:
        theta = np.deg2rad(max(self.tx.theta_div_deg, 0.5))
        G_tx = self.geom.G_tx_optics
        G_rx = self.geom.rx_concentrator_gain()
        phi = self.geom.phi_incident_deg
        Pi = self.geom.fov_window(phi)
        d = self.geom.distance_m
        denom = np.pi * d*d * (np.tan(theta)**2 + 1e-12)
        num = G_tx * G_rx * self.rx.A_pd_m2 * np.cos(np.deg2rad(phi))
        return Pi * max(num/denom, 0.0)
    def received_power_W(self, stochastic: bool=False) -> float:
        Pt = self.tx.Pt_w * self.tx.eta_t
        c = self.water.c_m1
        atten = np.exp(-c * self.geom.distance_m)
        G = self._geom_gain_ld() if self.tx.is_laser else self._geom_gain_led()
        turb = 1.0
        if stochastic and self.turb.scint_index > 0:
            turb = float(self.turb.fading_gain(size=1)[0])
        return Pt * atten * G * self.rx.eta_r * turb
    def noise_variances(self, Pr_W: float, bandwidth_Hz: float, rin: float|None, Idark_A: float) -> dict:
        R = self.rx.R_A_per_W
        B = bandwidth_Hz
        shot = 2*q*R*Pr_W*B
        thermal = 4*kB*self.rx.T*B / max(self.rx.R_load, 1e-3)
        dark = 2*q*Idark_A*B if Idark_A and Idark_A>0 else 0.0
        rin_var = (R*Pr_W)**2 * B * rin if rin is not None else 0.0
        return dict(shot=shot, thermal=thermal, dark=dark, rin=rin_var)
    def snr_db(self, bandwidth_Hz: float, rin: float|None=None, Idark_A: float=0.0) -> float:
        Pr = self.received_power_W()
        R = self.rx.R_A_per_W
        sig = (R*Pr)**2
        nv = self.noise_variances(Pr, bandwidth_Hz, rin, Idark_A)
        sigma2 = sum(nv.values())
        snr = sig / max(sigma2, 1e-30)
        return 10*np.log10(snr + 1e-30)
