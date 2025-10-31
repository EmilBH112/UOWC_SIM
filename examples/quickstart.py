import numpy as np
import matplotlib.pyplot as plt
from UOWC.media import WaterType
from UOWC.link import Link, Tx, Rx, Geometry, Turbulence
from UOWC.modulation import ber_ook_from_snr_db

waters = [
    WaterType.pure_sea_520nm(),
    WaterType.clear_ocean_520nm(),
    WaterType.coastal_ocean_520nm(),
    WaterType.turbid_harbor_520nm(),
]

tx = Tx(Pt_w=0.1, eta_t=0.9, semi_angle_deg=60, is_laser=False)
rx = Rx(R_A_per_W=0.2, A_pd_m2=1e-6, eta_r=0.9, T=300, R_load=50)
turb = Turbulence.model('lognormal', scint_index=0.1)
distances = np.linspace(1, 20, 100)

plt.figure()
for w in waters:
    snr = []
    for d in distances:
        geom = Geometry(distance_m=float(d), theta_tx_deg=30, phi_incident_deg=15,
                        fov_deg=30, G_tx_optics=1.0, n_concentrator=1.5)
        link = Link(w, tx, rx, geom, turb)
        snr.append(link.snr_db(bandwidth_Hz=1e6, rin=None, Idark_A=1e-9))
    plt.plot(distances, snr, label=w.name)
plt.xlabel("Distance (m)")
plt.ylabel("SNR (dB)")
plt.title("LED-PS: SNR vs distance, lognormal turbulence")
plt.legend()
plt.show()

plt.figure()
for w in waters:
    geom = Geometry(distance_m=10.0, theta_tx_deg=30, phi_incident_deg=15,
                    fov_deg=30, G_tx_optics=1.0, n_concentrator=1.5)
    link = Link(w, tx, rx, geom, turb)
    snr_db = link.snr_db(bandwidth_Hz=1e6, rin=None, Idark_A=1e-9)
    ber = ber_ook_from_snr_db(snr_db)
    plt.scatter([snr_db], [ber], label=w.name)
plt.yscale('log')
plt.xlabel("SNR (dB)")
plt.ylabel("BER (OOK)")
plt.title("OOK BER at 10 m across water types")
plt.legend()
plt.show()
