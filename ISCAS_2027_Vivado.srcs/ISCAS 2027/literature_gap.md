# Literature Gap and Scope Note

The current implementation is a reproducible engineering approximation, not a transcription of the paper's biological model. Appendix B has been transcribed and audited from the attached paper and enlarged source images; see `PAPER_EQUATION_AUDIT.md`.

Key open items:
- source-supported definition, units, and time course of `J_hv(t)` in B.2
- clarification of units/coupling between B.2 phototransduction calcium states and B.9 shell/free calcium states
- exact base intended for the B.5 `log` expression, and several symbols whose units are only implied
- numeric stimulus and response data for reproducing paper plots; available plots do not specify machine-readable samples or uncertainty bounds

The current provisional Python and passing baseline RTL have known structural
and parameter mismatches documented in the audit. No biological simulation
using an assumed stimulus should be represented as paper validation.
