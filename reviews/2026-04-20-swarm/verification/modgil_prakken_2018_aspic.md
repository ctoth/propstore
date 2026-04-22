# Modgil-Prakken 2018 ASPIC+ verification

Workstream items: T5.1, T3.8.

Opened page images:
- `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-011.png`.
- `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-020.png`.

Verified paper content:
- Definition 9 distinguishes undercuts from preference-dependent attacks: undercuts defeat directly, while preference-dependent attacks defeat only when the attacker is not strictly worse.
- Definitions 19-21 give elitist and democratic set orderings and last-link / weakest-link principles.

Implementation checked:
- `C:/Users/Q/code/argumentation/src/argumentation/aspic.py` for attack-to-defeat handling.
- `C:/Users/Q/code/argumentation/src/argumentation/preference.py` for strict partial order closure and set-comparison principles.
- `propstore/aspic_bridge/translate.py` and `propstore/aspic_bridge/projection.py` for preserving structured attacks, rule strengths, and claim identity through the propstore bridge.

Result: matches the opened PDF pages.
