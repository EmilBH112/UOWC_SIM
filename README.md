# UOWC_SIM — Underwater Optical Wireless Communication Simulator

A lightweight Python simulator for LED/laser underwater links:
attenuation (Beer–Lambert), turbulence fading (log-normal, generalized-gamma, Weibull),
receiver noise (shot/thermal/dark/RIN), optics geometry, and OOK/PPM BER.

**Why?** To quickly estimate received power, SNR, and BER across water types and distances.

## Install
```bash
pip install -r requirements.txt
```

## Quick start
```python
from UOWC.media import WaterType
from UOWC.link import Link, Tx, Rx, Geometry, Turbulence
from UOWC.modulation import ber_ook_from_snr_db, ppm_encode

water = WaterType.clear_ocean_520nm()
tx = Tx(Pt_w=0.1, eta_t=0.9, semi_angle_deg=60, is_laser=False)
rx = Rx(R_A_per_W=0.2, A_pd_m2=1e-6, eta_r=0.9, T=300, R_load=50)
geom = Geometry(distance_m=5.0, theta_tx_deg=30, phi_incident_deg=15, fov_deg=30,
                G_tx_optics=1.0, n_concentrator=1.5)
turb = Turbulence.model('lognormal', scint_index=0.1)

link = Link(water, tx, rx, geom, turb)
Pr_W = link.received_power_W()
snr_db = link.snr_db(bandwidth_Hz=1e6, rin=None, Idark_A=1e-9)
ber = ber_ook_from_snr_db(snr_db)
print(Pr_W, snr_db, ber)
```

See `examples/quickstart.py` for a sweep over distance and water types.

## Features
- Water presets: pure sea / clear ocean / coastal / turbid harbor @520 nm (α, β, c)
- Attenuation: Beer–Lambert `I(d,λ)=I0·e^{-c(λ)d}`
- Turbulence: log-normal, generalized-gamma, Weibull (normalized unit-mean fading)
- Sources: LED (Lambertian) vs laser (narrow beam) geometry
- Optics: receiver concentrator/FOV gain, expander hooks
- Noise: shot, thermal, dark, optional RIN
- Metrics: received power, SNR, BER (OOK; PPM helper)

## References
- Cochenour-style blue–green window & Beer–Lambert background
- Zayed & Shokair (2025), Scientific Reports — parameterizations used for examples
