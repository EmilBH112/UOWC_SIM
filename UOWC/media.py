"""
Water media presets at ~520 nm.

Each preset provides absorption (alpha), scattering (beta), and total attenuation
(c = alpha + beta) in m^-1 as commonly used with Beer–Lambert I(d)=I0·exp(-c·d).
You can extend this with wavelength-dependent tables or functions.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class WaterType:
    name: str
    alpha_m1: float
    beta_m1: float
    c_m1: float

    @staticmethod
    def pure_sea_520nm():
        return WaterType("Pure Sea (520 nm)", alpha_m1=0.04418, beta_m1=0.0009092, c_m1=0.0450892)
    @staticmethod
    def clear_ocean_520nm():
        return WaterType("Clear Ocean (520 nm)", alpha_m1=0.08642, beta_m1=0.01226, c_m1=0.09868)
    @staticmethod
    def coastal_ocean_520nm():
        return WaterType("Coastal Ocean (520 nm)", alpha_m1=0.2179, beta_m1=0.09966, c_m1=0.31756)
    @staticmethod
    def turbid_harbor_520nm():
        return WaterType("Turbid Harbor (520 nm)", alpha_m1=1.112, beta_m1=0.5266, c_m1=1.6386)
    @staticmethod
    def clear_ocean_520nm_as_default():
        return WaterType.clear_ocean_520nm()
