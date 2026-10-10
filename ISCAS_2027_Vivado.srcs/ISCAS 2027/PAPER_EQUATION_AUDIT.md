# Appendix B source transcription and implementation audit

## Source and evidence

Primary source: Payal Shah, Reena Sonkusare, and Surendra S. Rathod, “FinFET
based photoreceptor for silicon retina to reduce power consumption,”
*Biosensors and Bioelectronics: X* 14 (2023), article 100330,
doi:10.1016/j.biosx.2023.100330.

The attached PDF is present and its Appendix B headings/text were inspected.
The user supplied enlarged Appendix B images for printed pages 8–10; those
images resolve equations that are not recoverable by ordinary text extraction
from the PDF. Citations below use the printed page and Appendix B subsection.
The paper presents these equations without individual equation numbers, so
subsection labels (B.1–B.9) are the most precise equation references.

This is a transcription of what is legible in the supplied source images.
Where the source omits a definition or leaves notation/dimensions unclear,
that uncertainty is explicitly retained. A separate float64 transcription
was subsequently added in `paper_biological_model.py`; its existence does not
resolve missing source definitions or establish biological validity. No
equations were inferred from textbook models.

## Paper model transcription

### B.1 Membrane potential (printed p. 8)

The total current is

`I_ALL = I_photo + I_Kv + I_h + I_Ca + I_Cl(Ca) + I_K(Ca) + I_L + I_ex + I_ex2`

and the membrane equation and stated initial condition are

`C_m dV/dt = -I_ALL`, with `V(0) = -36.186` and `C_m = 0.02 nF`.

The voltage unit is inferred to be mV from the reversal potentials in B.3–B.8.
The paper does not print the unit next to `V(0)` in this line. The negative
sign in the membrane equation is preserved.

### B.2 Photocurrent / phototransduction (printed pp. 8–9)

The states and equations shown are:

```
dRh/dt   = J_hv - alpha1*Rh + alpha2*Rhi                  Rh(0) = 0
dRhi/dt  = alpha1*Rh - (alpha2 + alpha3)*Rhi              Rhi(0) = 0
dTr/dt   = epsilon*Rh*(Ttot - Tr) - beta1*Tr
           + tau2*PDE - tau1*Tr*(PDEtot - PDE)            Tr(0) = 0
dPDE/dt  = tau1*Tr*(PDEtot - PDE) - tau2*PDE              PDE(0) = 0
dCa/dt   = b*J - gammaCa*(Ca - C0)
           - k1*(eT - Cab)*Ca + k2*Cab                   Ca(0) = 0.3
dcGMP/dt = Amax/(1 + (Ca/Kc)^4) - cGMP*(Vbar - sigma*PDE)
                                                           cGMP(0) = 2.0
dCab/dt  = k1*(eT - Cab)*Ca - k2*Cab                    Cab(0) = 34.88
```

The auxiliary current-like signal and photocurrent are

```
J       = Jmax*(cGMP^3)/(cGMP^3 + 10^3)
I_photo = -J*(1 - exp((V - 8.5)/17))
```

Values and units printed alongside these equations:

| Symbol | Paper value | Printed unit / note |
|---|---:|---|
| alpha1 | 50 | s^-1 |
| alpha2 | 0.0003 | s^-1 |
| alpha3 | 0.03 | s^-1 |
| epsilon | 0.5 | s^-1 μM^-1 |
| Ttot | 1000 | μM |
| beta1 | 2.5 | s^-1 |
| tau1 | 0.2 | s^-1 μM^-1 |
| tau2 | 5 | s^-1 |
| PDEtot | 100 | μM is implied by the parameter line/context; the unit is not repeated clearly |
| gammaCa | 50 | s^-1 |
| C0 | 0.1 | μM |
| b | 0.25 | μM s^-1 pA^-1 |
| k1 | 0.2 | s^-1 μM^-1 |
| k2 | 0.8 | s^-1 |
| eT | 500 | μM |
| Vbar | 0.4 | s^-1 |
| Kc | 0.1 | unit not legible/stated in the parameter line |
| Amax | 65.6 | μM s^-1 |
| sigma | 1.0 | s^-1 μM^-1 |
| Jmax | 5040 | pA |

`J_hv` (the input driving Rh) is not defined or assigned a stimulus waveform
in the provided Appendix B images. The units of Rh, Rhi, Tr, PDE, cGMP, Cab,
and Kc are not all fully stated. Consequently, `J_hv(t)` and a unit-consistent
input cannot be chosen without additional source evidence.

### B.3 Hyperpolarization-activated current (printed p. 8)

```
alpha_h = 8/(exp((V + 78)/14) + 1)
beta_h  = 18/(exp((-V + 8)/19) + 1)

d/dt [C1, C2, O1, O2, O3]^T = M_h [C1, C2, O1, O2, O3]^T

M_h = [
 [-4 alpha_h,       beta_h,                 0,                 0,          0],
 [ 4 alpha_h, -(3 alpha_h + beta_h),    2 beta_h,               0,          0],
 [ 0,                3 alpha_h, -(2 alpha_h + 2 beta_h), 3 beta_h,          0],
 [ 0,                0,                2 alpha_h, -(alpha_h + 3 beta_h), 4 beta_h],
 [ 0,                0,                    0,             alpha_h,    -4 beta_h]
]

I_h = gbar_h*(O1 + O2 + O3)*(V - E_h)
```

Initial conditions: `C1=0.646`, `C2=0.298`, `O1=0.0517`,
`O2=0.00398`, `O3=0.000115`; `gbar_h=3.0 nS`; `E_h=-32 mV`.
The rate equations use V in mV by their printed constants. The rate unit is
not repeated in the equation block; seconds are inferred from the surrounding
parameter conventions.

### B.4 Delayed rectifier current (printed p. 9)

```
alpha_mKv = 5*(100 - V)/(exp((100 - V)/42) - 1)
beta_mKv  = 9*exp(-(V - 20)/40)
alpha_hKv = 0.15*exp(-V/22)
beta_hKv  = 0.4125/(exp((10 - V)/7) + 1)

dmKv/dt = alpha_mKv*(1 - mKv) - beta_mKv*mKv;  mKv(0)=0.430
dhKv/dt = alpha_hKv*(1 - hKv) - beta_hKv*hKv;  hKv(0)=0.999

I_Kv = gbar_Kv*mKv^3*hKv*(V - E_K)
gbar_Kv = 2.0 nS; E_K = -74 mV
```

### B.5 Calcium current (printed p. 9)

```
alpha_mCa = 3*(80 - V)/(exp((80 - V)/25) - 1)
beta_mCa  = 10/(1 + exp((V + 38)/7))
hCa       = exp((40 - V)/18)/(1 + exp((40 - V)/18))

dmCa/dt = alpha_mCa*(1 - mCa) - beta_mCa*mCa; mCa(0)=0.436
I_Ca = gbar_Ca*mCa^4*hCa*(V - E_Ca)
gbar_Ca = 0.7 nS
E_Ca = -12.5*log([Ca]s/[Ca]0); [Ca]0 = 1600 μM
```

The base of `log` is not stated. Do not silently replace it with log10 or
natural log without checking the cited Usui/Kamiyama model.

### B.6 Calcium-activated chloride current (printed p. 9)

```
mCl = 1/(1 + exp((0.37 - [Ca]s)/0.09))
I_Cl(Ca) = gbar_Cl*mCl*(V - E_Cl)
gbar_Cl = 2.0 nS; E_Cl = -20 mV
```

### B.7 Calcium-activated potassium current (printed p. 9)

```
alpha_mKCa = 15*(80 - V)/(exp((80 - V)/40) - 1)
beta_mKCa  = 20*exp(-V/35)
dmKCa/dt = alpha_mKCa*(1 - mKCa) - beta_mKCa*mKCa
mKCa(0) = 0.642
mKCa_s = [Ca]s/([Ca]s + 0.3)
I_KCa = gbar_KCa*mKCa^2*mKCa_s*(V - E_K)
gbar_KCa = 5.0 nS; E_K = -74 mV
```

### B.8 Leakage current (printed pp. 9–10)

```
I_L = g_L*(V - E_L)
g_L = 0.35 nS; E_L = -77 mV
```

### B.9 Intercellular calcium system (printed p. 10)

The printed equations are retained in the form shown, including the current
source term in the shell-calcium equation:

```
d[Ca]s/dt =
  -(I_Ca + I_ex + I_ex2)/(2*F*V1)*10^-6
  - D_Ca*S1/(delta*V1)*([Ca]s - [Ca]f)
  - Lb1*[Ca]s*(BL - [Cab]ls) + Lb2*[Cab]ls
  - Hb1*[Ca]s*(BH - [Cab]hs) + Hb2*[Cab]hs
  ([Ca]s(0)=0.0966)

d[Ca]f/dt =
  D_Ca*S1/(delta*V2)*([Ca]s - [Ca]f)
  - Lb1*[Ca]f*(BL - [Cab]lf) + Lb2*[Cab]lf
  - Hb1*[Ca]f*(BH - [Cab]hf) + Hb2*[Cab]hf
  ([Ca]f(0)=0.0966)

d[Cab]ls/dt = Lb1*[Ca]s*(BL - [Cab]ls) - Lb2*[Cab]ls
              ([Cab]ls(0)=80.929)
d[Cab]hs/dt = Hb1*[Ca]s*(BH - [Cab]hs) - Hb2*[Cab]hs
              ([Cab]hs(0)=29.068)
d[Cab]lf/dt = Lb1*[Ca]f*(BL - [Cab]lf) - Lb2*[Cab]lf
              ([Cab]lf(0)=80.929)
d[Cab]hf/dt = Hb1*[Ca]f*(BH - [Cab]hf) - Hb2*[Cab]hf
              ([Cab]hf(0)=29.068)

I_ex  = J_ex * exp(-(V + 14)/70)
        * ([Ca]s - Cae)/([Ca]s - Cae + K_ex)
I_ex2 = J_ex2
        * ([Ca]s - Cae)/([Ca]s - Cae + K_ex2)
```

Printed parameters:

| Symbol | Value | Printed unit |
|---|---:|---|
| F | 9.648 × 10^4 | C mol^-1 |
| V1 | 3.812 × 10^-13 | dm^3 |
| V2 | 5.236 × 10^-13 | dm^3 |
| D_Ca | 6 × 10^-8 | dm^2 s^-1 |
| delta | 3 × 10^-5 | dm |
| S1 | 3.142 × 10^-8 | dm^2 |
| Lb1 | 0.4 | s^-1 μM^-1 |
| Lb2 | 0.2 | s^-1 |
| Hb1 | 100 | s^-1 μM^-1 |
| Hb2 | 90 | s^-1 |
| BL | 500 | μM |
| BH | 300 | μM |
| J_ex | 20 | pA |
| J_ex2 | 20 | pA |
| K_ex | 2.3 | μM |
| K_ex2 | 0.5 | μM |
| Cae | 0.01 | μM |

## Blocker resolution from source evidence (2026-10-10)

This section separates what the Shah et al. paper states from dimensional
inferences and unresolved model choices. The attached PDF was inspected via
the supplied enlarged Appendix B pages and the article text/metadata
available in this session. The original PDF browser tab in Downloads reports
that it is outside a trusted folder; the source image for printed p. 10 is
not among the two persisted zoom files in this session. The earlier Appendix
B audit already transcribed its B.9 equations from the user-provided paper
pages. Cited-paper full texts were not obtained, so their metadata is not
being treated as equation-level evidence.

### `J_hv(t)` and the paper stimulus

| Evidence type | Finding | Source location |
|---|---|---|
| Confirmed equation | `J_hv` is an additive input to `dRh/dt = J_hv - alpha1*Rh + alpha2*Rhi`. The equation does not define `J_hv` further. | Shah et al., Appendix B.2, printed pp. 8–9 |
| Dimensional implication only | Because `alpha1*Rh` and `alpha2*Rhi` are rates, `J_hv` must have dimensions of `Rh/time`. If `Rh` is dimensionless, that reduces to inverse time. The paper does not state the unit or establish that `Rh` is dimensionless. | Same B.2 equation and its parameter line |
| Confirmed model limitation | B.2 lists rate constants and initial states but no mapping from optical power, photon flux, normalized light, or stimulus intensity to `J_hv`. No pulse/step amplitude, onset/offset, or time course for `J_hv(t)` is given in the inspected equation block. | Appendix B.2, printed pp. 8–9 |
| Figures/captions | The figure captions describe photoreceptor circuits and their output waveforms (Fig. 2(b), Fig. 3(d)); they do not define an input-light waveform or calibrate it to `J_hv`. The article text discusses stimulus strength/frequency qualitatively, without a numerical `J_hv(t)` specification. | Figs. 2–3 captions; Results and discussion text |
| Summary data | Tables 1–2 / the article’s reported-versus-observed current and voltage ranges do not provide time-stamped input samples or a transformation to `J_hv`. | Results section; Tables 1–2 |
| Cited model sources | The Appendix B heading attributes the equations to Usui et al. (1996) and Kamiyama et al. (2009). Metadata/abstract identifies the former as a horizontal-cell ionic-current model and the latter by title as a rod-photoreceptor-network study. The available text for neither cited work was sufficient to trace a numeric `J_hv` definition or rod stimulus. | Appendix B heading, printed p. 8; References section; cited DOI records below |
| Supplement/data availability | No supplementary file containing a stimulus trace was identified in the available article metadata. The article's Data availability statement says data will be made available on request; this does not establish that no author-held trace exists. | Article Data availability statement |

**Status: BLOCKED.** There is no source-supported exact unit, amplitude, waveform,
or time course for `J_hv(t)`. The relation required to proceed is an explicit
stimulus-to-`J_hv` mapping, including its dimensional convention and
time-series parameters. Author-provided MATLAB input/code or a supplement
containing the numerical stimulus and units would settle it. The float64
implementation's required `j_hv(t)` callable is therefore an interface for
future evidence, not a model default. Its synthetic zero input is not a
reconstruction of the paper experiment.

### B.2 calcium states versus B.9 calcium compartments

| Evidence type | Finding | Source location |
|---|---|---|
| Confirmed separate roles | B.2 `Ca` appears in the phototransduction/binding equations and controls the cGMP production term through `(Ca/Kc)^4`; `Cab` is its paired bound state. | Appendix B.2, printed pp. 8–9 |
| Confirmed separate roles | B.9 `[Ca]s` and `[Ca]f` exchange by diffusion, bind four low-/high-affinity buffer states, and the shell state receives `I_Ca+I_ex+I_ex2`. `[Ca]s` is also the calcium input to the Ca reversal potential and Ca-dependent channel expressions. | Appendix B.5–B.7, printed p. 9; B.9, printed p. 10 |
| Confirmed distinct initial values | B.2 has `Ca(0)=0.3` and `Cab(0)=34.88`; B.9 has `[Ca]s(0)=[Ca]f(0)=0.0966`, `[Cab]ls(0)=[Cab]lf(0)=80.929`, and `[Cab]hs(0)=[Cab]hf(0)=29.068`. These are not equal initializations of a single shared state. | B.2, printed pp. 8–9; B.9, printed p. 10 |
| Dimensional evidence | The B.2 parameter units (`C0` in μM; `gammaCa` in s^-1; `k1` in s^-1 μM^-1; `eT` in μM) imply `Ca` and `Cab` are concentrations in μM for the displayed terms to be dimensionally consistent. B.9 explicitly lists buffer and exchanger concentrations in μM; its calcium states are treated as μM by those equations. | B.2 parameter line, printed p. 9; B.9 parameter list, printed p. 10 |
| Missing coupling | No equation equates B.2 `Ca` with B.9 `[Ca]s` or `[Ca]f`, and no transfer term maps B.2 `Cab` to any of the B.9 buffer states. The supplied text does not specify an anatomical boundary, volume conversion, or cross-compartment flux connecting the two groups. | Compare the complete B.2 and B.9 equation blocks |

**Status: PARTIALLY RESOLVED.** The equations establish that the states play
different mathematical roles and carry different initial values. The safe
implementation choice is to retain them as distinct state groups, as the
float64 model currently does. The source does **not** establish whether they
represent anatomically distinct compartments that are coupled elsewhere, or
whether Appendix B combines disconnected subsystem equations. It gives no
valid conversion factor or coupling equation. Biological simulation that
depends on identifying the B.2 calcium with the B.9 shell/free concentrations
remains blocked. A source figure defining compartment geometry, the original
MATLAB state/coupling equations, or author clarification would resolve this.

### Calcium reversal-potential logarithm

| Evidence type | Finding | Source location |
|---|---|---|
| Confirmed equation | The source prints `E_Ca = -12.5 log([Ca]s/[Ca]0)` and lists `[Ca]0=1600 μM`; it does not print `ln`, `log10`, or another base marker. | Appendix B.5, printed p. 9 |
| Cited references | Shah et al. identify Appendix B as “reported in Usui et al. 1996 and Kamiyama et al. 2009.” The reference list identifies Usui et al. as “Reconstruction of retinal horizontal cell responses by the ionic current model,” *Vision Research* 36, 1711–1719, DOI [10.1016/0042-6989(96)00267-2](https://doi.org/10.1016/0042-6989(96)00267-2); and Kamiyama, Wu, and Usui as “Simulation analysis of bandpass filtering properties of a rod photoreceptor network,” *Vision Research* 49, 970–978, DOI [10.1016/j.visres.2009.03.003](https://doi.org/10.1016/j.visres.2009.03.003). | Appendix B heading, printed p. 8; References section |
| Retrieved source evidence | Bibliographic records and the 1996 abstract were available. The 1996 work is explicitly a horizontal-cell model, not itself a rod-photoreceptor paper. Full equation text from that paper was unavailable; the 2009 record identifies a rod-photoreceptor network but its equation text was also unavailable. | Crossref/OpenAlex/Semantic Scholar bibliographic metadata and 1996 abstract; cited DOI records above |

**Status: BLOCKED.** Neither the B.5 line nor the accessible evidence from the
cited works determines the operator base. The coefficient `12.5` may invite a
natural-log interpretation under a particular electrochemical convention,
but that is only a plausibility argument and is not sufficient evidence to
select it. The paper's numeric operating point cannot be used to disambiguate
the formula because no exact `E_Ca` reference value is reported. The existing
float64 implementation therefore requires an explicit `log_base` and retains
both branches. The original equation as implemented in the cited rod model
(or author-provided MATLAB source specifying `log`/`log10`) is needed to
resolve this item.

### Consequence for biological validation

The three source issues have distinct effects:

1. Without `J_hv(t)`, no paper-defined phototransduction trajectory or
   stimulus-response curve can be run.
2. Without the B.2/B.9 calcium mapping, the whole-cell calcium feedback and
   compartment dynamics cannot be claimed to form the paper's fully coupled
   biological model. Retaining the groups separately avoids an invented
   equality, but does not prove the coupling is complete.
3. Without the `E_Ca` logarithm base, the calcium current and therefore the
   membrane and shell-calcium trajectories are not uniquely determined.

Accordingly, equations can be unit-tested and a solver can be checked for
convergence under declared assumptions, but a paper-faithful response and
biological validation remain blocked.

## State and current meanings stated or implied by the notation

The paper does not provide a separate formal glossary. The physical meanings
below follow the equation names and dependencies; where the name is
insufficient to define a compartment, that limitation is stated.

| Symbol | Role in the paper equations |
|---|---|
| V | Photoreceptor membrane potential; mV is inferred from the current equations and reversal-potential units |
| I_ALL | Algebraic sum of the nine membrane-current components in B.1 |
| I_photo | Light/phototransduction-dependent photocurrent; negative sign and voltage dependence are explicit in B.2 |
| I_h | Hyperpolarization-activated current carried by open-state occupancy O1+O2+O3 |
| I_Kv | Delayed-rectifier potassium current, activated by mKv and inactivated by hKv |
| I_Ca | Calcium current, activated by mCa and hCa, and with reversal potential dependent on [Ca]s |
| I_Cl(Ca) | Calcium-activated chloride current, gate mCl depends on [Ca]s |
| I_K(Ca) | Calcium-activated potassium current, gate mKCa and calcium factor mKCa_s |
| I_L | Leakage current |
| I_ex, I_ex2 | Additional calcium/exchanger-like currents; exact biological names beyond the symbols are not expanded in Appendix B |
| Rh, Rhi | Phototransduction cascade states; the source does not spell out full molecular names in the equations |
| Tr | Transducer state in the PDE production/removal equations; exact physical species is not defined there |
| PDE | Phosphodiesterase-related state, inferred from its symbol and cGMP degradation coupling |
| Ca, Cab | B.2 calcium and bound-calcium states; units/compartment mapping to B.9 is not specified |
| cGMP | Cyclic-GMP-like state from its symbol; it controls J and has calcium/PDE-dependent dynamics |
| C1,C2 | Closed states in the five-state Ih kinetic scheme |
| O1,O2,O3 | Open states in the Ih kinetic scheme |
| mKv,hKv; mCa,hCa; mKCa | Activation/inactivation gates explicitly used in the corresponding B.4, B.5, B.7 currents |
| mCl | Algebraic calcium-dependent activation factor in B.6 |
| [Ca]s,[Ca]f | Shell and free calcium concentration states as indicated by B.9 notation; paper does not fully define compartment geometry in the supplied equations |
| [Cab]ls,[Cab]hs,[Cab]lf,[Cab]hf | Low-/high-affinity bound calcium states in shell/free compartments, inferred from subscripts and binding equations |
| J | Algebraic cGMP-dependent current-like quantity scaled by Jmax; J is distinct from input J_hv |
| J_hv | External phototransduction input in dRh/dt; waveform, units and physical stimulus mapping are not defined in supplied pages |

## Paper conditions and reported results

- Appendix B specifies initial conditions, not a complete time-varying
  stimulus. `J_hv` is present in the phototransduction equations but the
  supplied Appendix B pages do not define its waveform, amplitude, units, or
  relation to the paper's plotted/circuit light input.
- The article describes waveform-shape comparisons and gives a summary
  comparison in Table 3 (printed p. 7). Its figures are plots, not
  machine-readable time series. The visible material does not provide a
  numerical stimulus series, measured output samples, or error bars.
- The paper explicitly notes that circuit waveform magnitudes are scaled to
  be compatible with silicon device technology; visual shape agreement is
  not a numeric tolerance for this biological ODE.
- Table 3 (printed p. 7) compares operating mode, technology, supply,
  dissipation and waveform shape across a Liu MOSFET circuit, an Atwell
  biological experiment, the proposed MOSFET circuit and proposed FinFET
  circuit. The displayed circuit entries include 180 nm / <1.8 V for the
  cited MOSFET circuit, 180 nm / 1.5 V / 18 μW for the proposed MOSFET, and
  32 nm / 1.2 V / 1 pW for the proposed FinFET. The biological column has no
  device/power values. These are circuit-comparison results, not numerical
  validation of the ODE's time-series response.
- The results text says Table 1 summarizes ionic-model parameters and Table 2
  summarizes current/membrane-potential values, but the supplied enlarged
  images are Appendix B and Table 3; Table 1/2 values are not transcribed in
  this report. Appendix B itself does provide the equation parameters and
  initial conditions transcribed above.
- The exact analog stimulus used for the plots, output scaling, simulator
  settings, and full numeric data are not recoverable from the supplied
  equations/images alone. Digitization would be approximate and cannot
  resolve the unspecified input or model ambiguities.

## Equation audit: provisional Python and default baseline RTL

Agreement labels compare the implemented behavior with Appendix B, not
Python-vs-RTL. The two code paths can match one another and both differ from
the paper.

| Biological component | Source-paper equation | Paper parameters | Python implementation | RTL implementation | Agreement status | Discrepancy and significance | Proposed correction |
|---|---|---|---|---|---|---|---|
| Phototransduction | B.2 cascade for Rh, Rhi, Tr, PDE, Ca, cGMP, Cab; J(cGMP); voltage-dependent Iphoto | B.2 values above; J_hv waveform/units absent | `I_photo=g_photo*light`; other states absent | `I_photo=2000 pA*light`; no voltage dependence/cascade | MISMATCH | Core input-response mechanism and sign/voltage dependence differ | Separate paper model implementing all B.2 states after J_hv definition/units are confirmed |
| Membrane | B.1 I_ALL includes Iphoto, Kv, Ih, Ca, Cl(Ca), K(Ca), L, Iex, Iex2; C_m dV/dt=-I_ALL; V(0)=-36.186; C_m=.02nF | 20 pF, stated initial voltage (unit inferred mV) | `dV=-I_total/C_m` but only seven currents; V0=-60mV, C=30pF | same subset, Euler, V0=-60mV, cap 30pF, dt≈0.1ms | MISMATCH | Missing external currents and different capacitance/IC; current sum controls all dynamics | Preserve baseline; paper model uses all nine terms and paper values |
| Ih | B.3 five-state C1,C2,O1,O2,O3 matrix; current uses O1+O2+O3 | alpha/beta voltage rates, g=3nS, Eh=-32mV, all five ICs | one gate m_h sigmoid and g_h=120nS, Eh=-20mV; m_h0=.12 | one gate with LUT and same provisional g/E/IC | MISMATCH | Wrong state topology, activation kinetics, conductance, reversal, IC | Replace only in separate paper-model path; map five states directly |
| Kv | B.4 mKv and hKv kinetic gates; current g*mKv^3*hKv*(V-EK) | g=2nS, EK=-74mV, m0=.430, h0=.999 and voltage rates | one gate m_kv^3, g=250nS, EK=-80mV, m0=.18; no h gate | same one-gate cubic form; LUT gate; provisional constants | MISMATCH | Missing inactivation hKv and parameters/IC greatly differ | Implement independent mKv,hKv ODEs and source current |
| Ca current | B.5 mCa fourth power times hCa; ECa depends on log([Ca]s/[Ca]0) | g=.7nS, Ca0=1600μM, m0=.436; source alpha/beta/h equations | m_ca^3, constant Eca=+60mV, g=140nS, generic sigmoid/tau | m_ca^3, constant +60mV, g=140nS; fixed-point | MISMATCH | Gate exponent, h gate, reversal dependence, rates, IC and scale all differ | Paper model uses exact gates, fourth power and calcium-dependent Nernst-like expression; resolve log base |
| Cl(Ca) | B.6 mCl is logistic in [Ca]s; I=g*mCl*(V-ECl) | g=2nS, E=-20mV; calcium half-scale in exponent | m_clca*Ca_i/(Ca_i+K); g=90nS,E=-70mV | same ratio form using Ca_i and LUT-updated generic gate; g=90nS,E=-70mV | MISMATCH | Different state dependency, activation law, parameters, reversal | Use paper mCl([Ca]s) algebraically in independent model |
| K(Ca) | B.7 kinetic mKCa plus mKCa_s=[Ca]s/([Ca]s+.3); current g*mKCa^2*mKCa_s*(V-EK) | g=5nS, EK=-74mV, m0=.642; alpha/beta | m_kca*Ca_i/(Ca_i+K), first power gate, g=80nS, EK=-80mV | same ratio and first power; LUT gate and provisional constants | MISMATCH | Missing squared gate and kinetic rates; wrong calcium compartment, constant and reversal | Implement source gate and calcium activation exactly in separate model |
| Leakage | B.8 I_L=g_L*(V-E_L) | .35nS,-77mV | 20nS,-50mV | 20nS,-50mV | MISMATCH | Conductance is ~57x and reversal differs by 27mV | Set source values only in paper-model configuration |
| Calcium concentration/storage | B.2 Ca/Cab with cGMP feedback, plus B.9 shell/free Ca and four buffers; shell includes Ca/external-current term | B.2 and B.9 constants/ICs above | three simplified Ca_i/Ca_s/Ca_f ODEs, no buffers, different units/ICs | three mM states; recovery/transfers only; `i_ca_pA_q` unused | MISMATCH | Missing B.2 states/buffers/external currents; current contribution omitted, and state units differ | Model full coupled states independently; do not hide current term via fixed-point zeroing |
| Gate update / sigmoid | B.3–B.7 use distinct voltage-rate kinetics or concentration activation | Specific rates and initial values above | generic logistic steady-state and arbitrary relaxation taus for all five | 33-word logistic LUT, generic Euler relaxation; only one state per gate | MISMATCH | LUT neither in paper nor algebraically equivalent to source kinetics | Retain for baseline only; paper model evaluates source formulas without LUT |
| Arithmetic / discretization | Paper gives continuous-time ODEs; no Q format, word width, quantizer, update schedule, or dt in Appendix B | Not specified | float64; LSODA plus separate Euler/scheduler models; provisional equations | signed Q16.24; 40-bit wrap, truncation; dt≈0.1ms Euler | UNVERIFIED | Implementation choices cannot be validated as paper behavior; truncation/wrap add numerical error | Keep numeric scheme as declared engineering choice; quantify against source-equation float solver after model/input completion |
| Initial conditions | Explicit in B.1–B.9 as listed above | Voltage, all channel, phototransduction and calcium/buffer states | V=-60mV; made-up gates/calcium | encoded provisional equivalents | MISMATCH | Starting trajectory is not the published initial state | Load paper ICs only in separate source model |
| Stimulus | B.2 includes J_hv; paper output plots/table are not a quantified input trace | No J_hv waveform/amplitude/units found in supplied Appendix B | synthetic normalized dark/step/pulse/ramp stimuli | normalized raw-Q dark/step/pulse | UNVERIFIED | Cannot reproduce published response from labels “step” or “light” alone | Obtain J_hv definition/figure stimulus or cited source details before simulation |

The preceding comparison intentionally describes the **provisional
engineering model and RTL** and does not imply that they have become
paper-faithful. The separate float64 implementation now transcribes the
equations visible in B.1–B.9. It keeps B.2 `Ca`/`Cab` distinct from the B.9
`[Ca]s`/`[Ca]f` and buffers, because the source pages do not state an
identification or conversion between them. It requires an explicit `J_hv(t)`
callable and an explicit natural- or base-10 logarithm choice; these are
caller-selected branches, not source-resolved defaults.

### Separate source-equation implementation status

| Component | Implementation status | Remaining source qualification |
|---|---|---|
| B.1 membrane and all nine current terms | Transcribed and computed from one current state | Current polarity/units follow the printed equations; `V` in mV is inferred from reversal potentials |
| B.2 phototransduction states, algebraic `J`, and voltage-dependent `I_photo` | Transcribed as written; tests distinguish `J` from membrane `I_photo` | `J_hv` units, amplitude, stimulus waveform, and some state units are not stated |
| B.3 Ih five-state matrix | Transcribed; a test checks the matrix derivative sum is zero | Time units inferred from rate constants |
| B.4 Kv, B.5 Ca and B.7 KCa gates | Transcribed; alpha-rate removable singularities use mathematical limits | The paper's `E_Ca` logarithm base remains unspecified; both branches are explicit |
| B.6 chloride activation | Transcribed algebraically from `[Ca]s` | Concentration units assumed to be the B.9 printed μM |
| B.9 calcium shell/free and four buffers | Transcribed separately, including the printed current-source term and `I_ex`/`I_ex2` | B.2/B.9 calcium relationship, geometry, and cross-coupling are not stated |
| Numerical integration | SciPy DOP853 wrapper with caller-selected tolerances and maximum step | Solver options are engineering choices; invalid/nonpositive shell calcium raises rather than being clipped |

The separate parameter module preserves the listed Appendix B values.
`Kc=0.1` is stored as the unqualified `Kc_value` because its unit was not
legible/explicit in the parameter line. Printed and inferred units remain
identified in the transcription above.

## Specific implementation approximation findings

- **Sigmoid LUT:** the 33-entry table is an implementation approximation and
  is not supported by Appendix B. Appendix B instead has explicit alpha/beta
  kinetics, a three-open-state Ih chain, and a calcium-dependent Cl activation.
- **Q16.24:** a hardware representation absent from the paper. Its wrap and
  truncation are engineering choices; their numerical errors have not been
  measured against a source-equation implementation. They must not be called
  source-paper behavior.
- **Omitted calcium-current contribution:** `calcium_dynamics.v` ignores
  `i_ca_pA_q`. That is not supported by the paper: B.9 explicitly includes
  `(I_Ca + I_ex + I_ex2)` in the shell-calcium equation. It cannot be justified
  as “sub-LSB” relative to the source model. Its eventual fixed-point
  representability requires a dimensional conversion and range analysis.
- **No equation changes made:** the currently passing RTL and its
  bit-accurate Python mirror are retained unchanged as an engineering
  baseline. A scientifically grounded correction belongs in separate files.

## Discrepancies ranked by importance

1. **Critical scientific mismatch:** current phototransduction is a direct
   light gain rather than Appendix B's cascade; `J_hv` stimulus is missing.
2. **Critical scientific mismatch:** five-state Ih and distinct Kv/Ca/KCa
   gate kinetics have been replaced by generic single-gate LUT dynamics.
3. **Critical scientific mismatch:** the current inventory omits Iex/Iex2,
   buffer states, and most of the source calcium system; the RTL drops the
   Ca-current concentration term.
4. **High:** source conductances, reversals, capacitance, initial conditions,
   current dependencies and gate exponents differ substantially.
5. **High:** unit and coupling ambiguity across the B.2 and B.9 calcium
   subsystems, plus unspecified `log` base and missing J_hv units.
6. **Medium engineering:** Q16.24 truncation/wrap, LUT lookup and Euler update
   error have only been compared against the matching RTL mirror, not against
   a source-equation float model.
7. **Medium evidence limitation:** article figures provide qualitative
   waveforms, not numerical sample tables or stated error bars/tolerances.

## Validation and corrections

The separate implementation has been exercised in a 5 ms synthetic zero-input
solver-convergence screen, with both possible `E_Ca` logarithm bases selected
explicitly. Against a tighter DOP853 reference, maximum-step sweeps differed
by at most `2.28e-13` across endpoint states. Tolerance sweeps ranged from
`9.95e-14` to `1.35e-10`; the largest difference was the deliberately loose
base-10 case (`rtol=1e-5`). This shows numerical consistency for that short
synthetic trajectory only. It is not a paper stimulus, does not resolve the
logarithm base, and is not biological validation. Reproduce with
`run_paper_model_convergence.py`; settings and per-case results are in
`results/metrics/paper_model_solver_convergence.csv`. The CSV exports the
endpoint difference for every state; the aggregate maximum is an unscaled
diagnostic across variables with different units and must not be interpreted
as one physically meaningful error norm.

An exploratory larger-step attempt produced a solver trial state with
nonpositive `[Ca]s`, outside the domain of the calcium-reversal logarithm.
The implementation raises on this invalid domain instead of clipping it.
The recorded convergence sweep uses a smaller maximum step.

The next scientific step remains obtaining source-supported `J_hv(t)`, its
units/stimulus, and clarification of the calcium-state definitions and
logarithm convention. Only then can the paper stimulus be simulated and
compared with published results. Any plot digitization must be labeled
approximate. Do not modify the currently passing baseline RTL until source
definitions and a separate correction plan are justified.

Bibliographic metadata was checked for the two works cited with Appendix B:
Usui et al. (1996), “Reconstruction of retinal horizontal cell responses by
the ionic current model,” *Vision Research* 36, 1711–1719,
doi:10.1016/0042-6989(96)00267-2; and Kamiyama, Wu, and Usui (2009),
“Simulation analysis of bandpass filtering properties of a rod
photoreceptor network,” *Vision Research* 49, 970–978,
doi:10.1016/j.visres.2009.03.003. Full text of those cited works was not
retrieved during this step, so they have not been treated as evidence for
missing stimulus or unit/log definitions.

## Phase 4 checklist

| Item | Status | Evidence / blocker |
|---|---|---|
| Confirm and read attached paper / Appendix B | COMPLETE | Attachment present; equations checked against enlarged user-provided pages 8–10 |
| Transcribe equations, listed parameters and initial conditions | COMPLETE | This document, B.1–B.9; unprinted units/undefined symbols remain flagged |
| Implement separate double-precision source-equation transcription | COMPLETE | `paper_biological_model.py` and `paper_biological_parameters.py`; eight focused tests pass |
| Numerical convergence of implemented transcription | COMPLETE, LIMITED | 5 ms synthetic zero-input DOP853 comparison, with both explicit log branches; numerical consistency only |
| Inspect requested Python and baseline RTL | COMPLETE | Source files reviewed; mismatches listed in audit table |
| Determine paper stimulus conditions | BLOCKED | `J_hv(t)` and the plotted experiment input are not numerically specified in the supplied source material |
| Resolve B.2/B.9 state units/coupling and log base | BLOCKED | Source excerpts do not specify the needed mapping/convention |
| Run paper-equation biological response | BLOCKED | Do not fabricate `J_hv` or merge the distinct/unclear B.2 and B.9 calcium states |
| Compare against published numeric traces | BLOCKED | Figures are plots without source numeric samples/uncertainty; digitization would be approximate and stimulus is missing |
| Separate continuous/discrete vs fixed-point error | PENDING | Requires source definitions and a meaningful operating trajectory |
| Preserve passing RTL baseline | COMPLETE | No RTL, current model, or fixed-point reference implementation changed |
| Run Python regression tests | COMPLETE | 24 passed in the latest `python -m pytest -q` run, including eight focused new tests |
| Phase 4 biological-fidelity objective | PENDING | Source audit complete; fidelity is not established |
