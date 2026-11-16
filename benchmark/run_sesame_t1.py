"""Sesame (NIST) side of the benchmark: tutorial 1, 1D CdTe-like homojunction, unchanged physics."""
import sys, numpy as np, sesame

L = 3e-4  # cm
x = np.concatenate((np.linspace(0, 1.2e-4, 300, endpoint=False), np.linspace(1.2e-4, L, 150)))
s = sesame.Builder(x, T=300)
s.add_material({'Nc': 8e17, 'Nv': 1.8e19, 'Eg': 1.5, 'affinity': 3.9, 'epsilon': 9.4,
                'mu_e': 100, 'mu_h': 100, 'tau_e': 10e-9, 'tau_h': 10e-9, 'Et': 0})
junction = 50e-6  # 0.5 um
s.add_donor(1e17, lambda p: p < junction)
s.add_acceptor(1e15, lambda p: p >= junction)
s.contact_type('Ohmic', 'Ohmic')
s.contact_S(1e7, 0, 0, 1e7)
phi, alpha = 1e17, 2.3e4
s.generation(lambda xx, yy: phi * alpha * np.exp(-alpha * xx))
V = np.round(np.arange(0, 1.001, 0.01), 3)
j = sesame.IVcurve(s, V, 'bench_t1_tmp', verbose=False) * s.scaling.current * 1e3  # mA/cm2
np.savetxt(sys.argv[1], np.column_stack([V, j]), header='V_volt J_mA_cm2 (Sesame sign convention)', fmt='%.6e')
print('saved', len(V), 'points; J(0) =', j[0])
