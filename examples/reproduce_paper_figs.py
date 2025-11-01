# Reproduce Zayed & Shokair (2025) style curves with documented equations.
# See module docstring for model alignment.
import os
import numpy as np
import matplotlib.pyplot as plt
import yaml
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

def make_link(w, d_m, turb):
    tx = Tx(Pt_w=cfg["transmitter"]["Pt_W"], eta_t=cfg["transmitter"]["eta_t"],
            semi_angle_deg=cfg["transmitter"]["led_semi_angle_deg"],
            is_laser=cfg["transmitter"]["is_laser"],
            theta_div_deg=cfg["transmitter"]["laser_div_deg"])
    rx = Rx(R_A_per_W=cfg["receiver"]["R_A_per_W"], A_pd_m2=cfg["receiver"]["A_pd_m2"],
            eta_r=cfg["receiver"]["eta_r"], T=cfg["receiver"]["T_K"],
            R_load=cfg["receiver"]["R_load_ohm"])
    geom = Geometry(distance_m=d_m, theta_tx_deg=cfg["geometry"]["theta_tx_deg"],
                    phi_incident_deg=cfg["geometry"]["phi_incident_deg"],
                    fov_deg=cfg["receiver"]["FOV_deg"], G_tx_optics=cfg["geometry"]["G_tx_optics"],
                    n_concentrator=cfg["receiver"]["n_concentrator"])
    return Link(w, tx, rx, geom, turb)

BW = cfg["bandwidth_Hz"]
Idark = cfg["receiver"]["Idark_A"]; rin = cfg["receiver"]["rin"]
Pbg = cfg["receiver"]["Pbg_W"]; M = cfg["receiver"]["apd_M"]; F = cfg["receiver"]["apd_F_excess"]

# 1) SNR vs distance with log-normal turbulence
_, turb = ("lognormal", Turbulence.model("lognormal", scint_index=0.1))
D = np.linspace(cfg["sweep"]["d_min_m"], cfg["sweep"]["d_max_m"], cfg["sweep"]["d_points"])
plt.figure()
for w in waters:
    snr = []
    for d in D:
        link = make_link(w, d, turb)
        snr.append(link.snr_db(BW, rin=rin, Idark_A=Idark, Pbg_W=Pbg, R_apd_M=M, F_excess=F))
    np.savetxt(f"results/snr_vs_distance__{w.name.replace(' ','_')}.csv",
               np.c_[D, snr], delimiter=",", header="distance_m,snr_dB", comments="")
    plt.plot(D, snr, label=w.name)
plt.xlabel("Distance (m)"); plt.ylabel("SNR (dB)")
plt.title("LED-PS: SNR vs distance (log-normal scint_index=0.1)")
plt.legend(); plt.tight_layout()
plt.savefig("results/fig_snr_vs_distance.png", dpi=160)

# 2) Pr vs distance (no turbulence)
plt.figure()
for w in waters:
    pr = []
    for d in D:
        link = make_link(w, d, Turbulence.model("lognormal", scint_index=0.0))
        pr.append(link.received_power_W(stochastic=False))
    np.savetxt(f"results/pr_vs_distance__{w.name.replace(' ','_')}.csv",
               np.c_[D, pr], delimiter=",", header="distance_m,Pr_W", comments="")
    plt.plot(D, pr, label=w.name)
plt.yscale("log"); plt.xlabel("Distance (m)"); plt.ylabel("Pr (W)")
plt.title("Received optical power vs distance (no fading)")
plt.legend(); plt.tight_layout()
plt.savefig("results/fig_pr_vs_distance.png", dpi=160)

# 3) BER snapshot at 10 m
plt.figure()
for w in waters:
    link = make_link(w, 10.0, Turbulence.model("lognormal", scint_index=0.1))
    snr_db = link.snr_db(BW, rin=rin, Idark_A=Idark, Pbg_W=Pbg, R_apd_M=M, F_excess=F)
    ber = ber_ook_from_snr_db(snr_db)
    plt.scatter([snr_db], [ber], label=w.name)
plt.yscale("log"); plt.xlabel("SNR (dB)"); plt.ylabel("BER (OOK)")
plt.title("OOK BER at 10 m across water types")
plt.legend(); plt.tight_layout()
plt.savefig("results/fig_ber_at_10m.png", dpi=160)
