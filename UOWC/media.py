from dataclasses import dataclass

"""
Water media presets at ~520 nm aligned to Zayed & Shokair (2025).

This exposes Beer–Lambert LOS attenuation with c(λ)=a(λ)+b(λ).
Use these factories to obtain per-water-type (α,β,c) values at λ≈520 nm (Table 3).
Backward-compatible accessors are provided for alpha_m1/beta_m1 and a default alias.
"""
from .iop_tables import (
    pure_sea_520nm as _ps, clear_ocean_520nm as _co,
    coastal_ocean_520nm as _cc, turbid_harbor_520nm as _th
)

@dataclass(frozen=True)
class WaterType:
    a_m1: float
    b_m1: float
    name: str

    # Back-compat properties for older code paths
    @property
    def alpha_m1(self) -> float:
        return self.a_m1

    @property
    def beta_m1(self) -> float:
        return self.b_m1

    @property
    def c_m1(self) -> float:
        return self.a_m1 + self.b_m1

    # --- Paper presets (λ ≈ 520 nm) ---
    @staticmethod
    def pure_sea_520nm():
        """Table 3 preset (λ≈520 nm)."""
        i = _ps();   return WaterType(a_m1=i.a_m1, b_m1=i.b_m1, name=i.name)

    @staticmethod
    def clear_ocean_520nm():
        """Table 3 preset (λ≈520 nm)."""
        i = _co();   return WaterType(a_m1=i.a_m1, b_m1=i.b_m1, name=i.name)

    @staticmethod
    def coastal_ocean_520nm():
        """Table 3 preset (λ≈520 nm)."""
        i = _cc();   return WaterType(a_m1=i.a_m1, b_m1=i.b_m1, name=i.name)

    @staticmethod
    def turbid_harbor_520nm():
        """Table 3 preset (λ≈520 nm)."""
        i = _th();   return WaterType(a_m1=i.a_m1, b_m1=i.b_m1, name=i.name)

    # Legacy alias retained for compatibility with earlier examples
    @staticmethod
    def clear_ocean_520nm_as_default():
        return WaterType.clear_ocean_520nm()
