# Rod-Photoreceptor Model Equations

**Status: provisional implementation; source audit complete, biological model mismatches confirmed.** The equations below describe the equations currently present in the initial Python code and are not a transcription of Shah et al. Appendix B. The paper's source equations, parameters, initial conditions, and a component-by-component comparison are in `PAPER_EQUATION_AUDIT.md`.

## Membrane equation

The membrane voltage is driven by the net current budget:

`dV/dt = -(I_photo + I_h + I_Kv + I_Ca + I_ClCa + I_KCa + I_L) / C_m`

## Ionic currents

- `I_h = g_h * m_h * (V - E_h)`
- `I_Kv = g_Kv * m_Kv^3 * (V - E_K)`
- `I_Ca = g_Ca * m_Ca^3 * (V - E_Ca)`
- `I_ClCa = g_ClCa * m_ClCa * (Ca_i / (Ca_i + K_ClCa)) * (V - E_Cl)`
- `I_KCa = g_KCa * m_KCa * (Ca_i / (Ca_i + K_KCa)) * (V - E_K)`
- `I_L = g_L * (V - E_L)`

## Gating dynamics

Each gating variable follows a first-order relaxation to a voltage-dependent steady state:

`dm/dt = (m_inf(V) - m) / tau_m`

with

`m_inf(V) = 1 / (1 + exp(-(V - V_half)/k))`

## Calcium dynamics

The calcium subsystem is represented with a compact ionic balance and storage states:

`dCa_i/dt = -alpha_Ca * I_Ca - beta_Ca * (Ca_i - Ca_rest)`
`dCa_s/dt = 0.5 * (Ca_i - Ca_s)`
`dCa_f/dt = 0.25 * (Ca_s - Ca_f)`

## Documentation note

The current code also assumes a direct normalized-light photocurrent `I_photo = g_photo * light`, sigmoid gating curves for every gate, and simplified calcium-state equations. These choices are not established from the paper and remain experimental assumptions. In particular, the omitted/unclear phototransduction states, current sign convention, calcium equations, units, and initial conditions must be resolved from the primary source before this can be called the scientific reference model.

The equations are preserved here to make the current implementation auditable, not to assert biological accuracy. Outputs and metrics generated from them are provisional engineering checks only.
