from dataclasses import dataclass

@dataclass(frozen=True)
class IOP:
    """
    Inherent optical properties (IOPs) at λ ≈ 520 nm, per Zayed & Shokair (2025), Table 3.
    a_m1: absorption [m^-1]
    b_m1: scattering [m^-1]
    c_m1 = a_m1 + b_m1 (Beer–Lambert LOS factor exp(-c*d))
    """
    a_m1: float
    b_m1: float
    name: str
    @property
    def c_m1(self) -> float:
        return self.a_m1 + self.b_m1

def pure_sea_520nm() -> IOP:
    # Table 3 (λ = 520 nm)
    return IOP(a_m1=0.04418, b_m1=0.0009092, name="Pure Sea (520 nm)")

def clear_ocean_520nm() -> IOP:
    return IOP(a_m1=0.08642, b_m1=0.01226, name="Clear Ocean (520 nm)")

def coastal_ocean_520nm() -> IOP:
    return IOP(a_m1=0.2179, b_m1=0.09966, name="Coastal Ocean (520 nm)")

def turbid_harbor_520nm() -> IOP:
    return IOP(a_m1=1.112, b_m1=0.5266, name="Turbid Harbor (520 nm)")
