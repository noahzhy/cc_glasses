"""Reproduce static E7 protection and front-end sensitivity calculations."""

import json
from pathlib import Path

import numpy as np
from scipy.signal import TransferFunction, step

ROOT = Path(__file__).resolve().parents[1]


def calculate():
    rows = []
    for gbw in [5e6, 10e6]:
        for ci in [20e-12, 50e-12, 100e-12]:
            for cf in [20.9e-12, 23.1e-12]:
                r, w = 100e3, 2 * np.pi * gbw
                s = 2j * np.pi * np.logspace(3, 8, 20000)
                loop = (w / s) * (1 + s * r * cf) / (1 + s * r * (cf + ci))
                k = np.argmin(abs(abs(loop) - 1))
                model = TransferFunction(
                    [r * w], [r * (cf + ci), 1 + w * r * cf, w]
                )
                t = np.linspace(0, 100e-6, 20001)
                _, y = step(model, T=t)
                bad = np.flatnonzero(abs(y / r - 1) > 1 / 8192)
                rows.append(
                    dict(
                        gbw_hz=gbw,
                        cin_pf=ci * 1e12,
                        cf_pf=cf * 1e12,
                        phase_margin_deg=float(
                            180 + np.angle(loop[k], deg=True)
                        ),
                        settle_us=float(t[bad[-1] + 1] * 1e6),
                    )
                )
    result = dict(
        model="Idealized single-pole sensitivity, not a silicon guarantee",
        tia=rows,
        tps2553_current_ma=dict(
            min=25230 / (111.1**1.016),
            nom=23950 / (110**0.977),
            max=22980 / (108.9**0.94),
        ),
        u19_trip_v=[
            3.3 * (1.04 - 0.009) * (1 + 198 / 10100),
            3.3 * (1.04 + 0.009) * (1 + 202 / 9900) + 1.5e-6 * 202,
        ],
        led_nominal_ma=1.208 * 43.8 / 2.67,
        adc_acquisition_us=61.5 / 12,
        adc_conversion_us=74 / 12,
        bias_tau_ms=5.0,
    )
    (ROOT / "review/circuit_calculations.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )


if __name__ == "__main__":
    calculate()
