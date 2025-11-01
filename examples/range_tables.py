"""
Compute maximum range for the three thresholds used in Zayed & Shokair (2025):
 - Receiver sensitivity: Pr ≥ −53.4 dBm
 - BER target: BER ≤ 1e−5  (OOK, BER ≈ Q(√SNR))
 - SNR target: SNR ≥ 50 dB
Outputs a Markdown table under results/range_tables.md.
"""
import os, numpy as np, yaml
from UOWC.media import WaterType
from UOWC.link import Link, Tx, Rx, Geometry, Turbulence
from UOWC.modulation import ber_ook_from_snr_db

with open("configs/paper_2025_defaults.yaml", "r") as f:
    cfg = yaml.safe_load(f)

os.makedirs("results", exist_ok=True)
waters = [
    WaterType.pure_sea_520nm(),
    WaterType.clear_ocean_520nm(),
    WaterType.coastal_ocean_520nm(),
    WaterType.turbid_harbor_520nm(),
]
BW = cfg["bandwidth_Hz"][email protected]
Idark = cfg["receiver"]["Idark_A"]; rin = cfg["receiver"]["rin"]
Pbg = cfg["receiver"]["Pbg_W"]; M = cfg["receiver"]["apd_M"]; F = cfg["receiver"]["apd_F_excess"]

def make_link(w, d_m):
    tx = Tx(Pt_w=cfg["transmitter"]["Pt_W"], eta_t=cfg["transmitter"]["eta_t"],
            semi_angle_deg=cfg["transmitter"]["led_semi_angle_deg"],
            is_laser=cfg["transmitter"]["is_laser"], theta_div_deg=cfg["transmitter"]["laser_div_deg"])
    rx = Rx(R_A_per_W=cfg["receiver"]["R_A_per_W"], A_pd_m2=cfg["receiver"]["A_pd_m2"],
            eta_r=cfg["receiver"]["eta_r"], T=cfg["receiver"]["T_K"], R_load=cfg["receiver"]["R_load_ohm"])
    geom = Geometry(distance_m=d_m, theta_tx_deg=cfg["geometry"]["theta_tx_deg"],
                    phi_incident_deg=cfg["geometry"]["phi_incident_deg"],
                    fov_deg=cfg["receiver"]["FOV_deg"], G_tx_optics=cfg["geometry"]["G_tx_optics"],
                    n_concentrator=cfg["receiver"]["n_concentrator"])
    return Link(w, tx, rx, geom, Turbulence.model("lognormal", scint_index=0.1))

def ok_power(link):
    pr_W = link.received_power_W(stochastic=False)
    pr_dBm = 10*np.log10(max(pr_W,1e-30)/1e-3)
    return pr_dBm >= cfg["thresholds"]["rx_sensitivity_dBm"]

def ok_snr(link):
    snr = link.snr_db(BW, rin=rin, Idark_A=Idark, Pbg_W=Pbg, R_apd_M=M, F_excess=F)
    return snr >= cfg["thresholds"]["snr_target_dB"]

def ok_ber(link):
    snr = link.snr_db(BW, rin=rin, Idark_A=Idark, Pbg_W=Pbg, R_apd_M=M, F_excess=F)
    return ber_ook_from_snr_db(snr) <= cfg["thresholds"]["ber_target"]

def find_max(w, pred, dmax=60.0, step=0.1):
    d = cfg["sweep"]["d_min_m"]; last_ok = None
    while d <= dmax:
        if pred(make_link(w, d)):
            last_ok = d
        d += step
    return last_ok or 0.0

rows = []
for w in waters:
    rows.append((w.name, find_max(w, ok_power), find_max(w, ok_ber), find_max(w, ok_snr)))

md = ["| Water Type | Ps≥−53.4 dBm (m) | BER≤1e−5 (m) | SNR≥50 dB (m) |",
      "|---|---:|---:|---:|"]
for name, a, b, c in rows:
    md.append(f"| {name} | {a:.1f} | {b:.1f} | {c:.1f} |")
with open("results/range_tables.md", "w") as f:
    f.write("
".join(md))
print("Wrote results/range_tables.md")
