from pathlib import Path

import matplotlib.pyplot as plt

from photoreceptor_reference import save_reference_trace, simulate_reference_model

BASE_DIR = Path(__file__).resolve().parent
PLOT_DIR = BASE_DIR / "results" / "plots"


def generate_provisional_reference_figures() -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    result = simulate_reference_model(
        stimulus={"type": "pulse", "amplitude": 0.2, "t_on": 0.2, "t_off": 0.5},
        t_end=1.0,
        dt=1e-4,
    )
    save_reference_trace(result, "provisional_pulse_reference.csv")
    time_ms = result["time"] * 1e3

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(time_ms, result["light"])
    ax.set(xlabel="Time (ms)", ylabel="Normalized light input", title="Experimental stimulus (not a paper waveform)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "experimental_stimulus.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(time_ms, result["V"] * 1e3)
    ax.set(xlabel="Time (ms)", ylabel="Membrane voltage (mV)", title="Provisional model: membrane voltage")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "provisional_membrane_voltage.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    for name in ("I_photo", "I_h", "I_kv", "I_ca", "I_clca", "I_kca", "I_l"):
        ax.plot(time_ms, result[name] * 1e12, label=name)
    ax.set(xlabel="Time (ms)", ylabel="Current (pA)", title="Provisional model: current traces")
    ax.legend(ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "provisional_currents.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    for name in ("m_h", "m_kv", "m_ca", "m_clca", "m_kca"):
        ax.plot(time_ms, result[name], label=name)
    ax.set(xlabel="Time (ms)", ylabel="Gate state", title="Provisional model: gating states")
    ax.legend(ncol=2)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "provisional_gating_states.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    for name in ("Ca_i", "Ca_s", "Ca_f"):
        ax.plot(time_ms, result[name] * 1e3, label=name)
    ax.set(xlabel="Time (ms)", ylabel="Calcium (mM; provisional units)", title="Provisional model: calcium states")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "provisional_calcium_states.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(time_ms, result["I_total"] * 1e12, label="I_total")
    ax.set(xlabel="Time (ms)", ylabel="Current (pA)", title="Provisional model: total current")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "provisional_total_current.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    generate_provisional_reference_figures()
    print(f"Saved provisional plots under {PLOT_DIR}")
