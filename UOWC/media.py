# uowc/media.py                             # This is just an a,b,c holder for now waiting for formulas
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class WaterMedium:
    """
    Inherent optical properties for a single wavelength (scalar model).
    a: absorption [m^-1]
    b: scattering [m^-1]
    c: attenuation = a + b [m^-1]  (Beer–Lambert LOS factor exp(-c*d))
    Notes:
      - Following common UOWC practice of using an effective c for first-cut LOS. 
      - Populate from Jerlov types / literature for your chosen λ (e.g., 450–550 nm).
    """
    a: float
    b: float
    name: Optional[str] = None

    @property
    def c(self) -> float:
        return self.a + self.b


# --- Quick presets (illustrative placeholders) ---
# Replace with values at your chosen wavelength from literature tables.
# Zayed & Shokair vary water type (pure/coastal/harbor) and analyze impact on link; 
# set these from their tables/plots when you pin λ. [Scientific Reports, 2025]
PURE_SEA = WaterMedium(a=0.035, b=0.025, name="Pure Sea (example)")
CLEAR_COASTAL = WaterMedium(a=0.06, b=0.08, name="Clear Coastal (example)")
TURBID_HARBOR = WaterMedium(a=0.19, b=0.50, name="Turbid Harbor (example)")
