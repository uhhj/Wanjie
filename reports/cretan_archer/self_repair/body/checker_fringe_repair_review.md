# Two hidden-patch checker fringes repaired

An independent review identified two RGB contaminants, not transparent holes: the exposed pelvis cloth margin at near elbow -20 degrees and the far torso margin next to the ivory sleeve at far shoulder +20 degrees. The far-shoulder probe had alpha 252..255 and zero transparent pixels; the visible checker was baked into the tool's RGB output.

The compositor now extrapolates adjacent genuine generated material only into classified neutral checker pixels within the two inspected narrow regions. Pelvis uses neighboring cream tunic cloth (462 RGB pixels); torso uses neighboring brown leather at the generated vest's edge (558 RGB pixels). The donor maps record the actual source-canvas coordinate sampled for every corrected pixel. No further image-generation call was made.

All geometry masks and alpha values remain unchanged. Only already-added hidden patch RGB is eligible. Existing source-owned pixels, the approved Body, all other parts and frozen sources are unchanged; the compositor asserts these invariants and reruns frozen-hash verification.

`checker_fringe_repair_combat_review.png` shows actual body heights 256px and 192px on gray and blue, with enlarged diagnostics below. The white/gray checker strips are gone. Cloth and sleeve remain visibly continuous, and neither test exposes a detached limb or a transparent hole. The local extrapolation has slight row texture at high magnification; it is not a combat-scale blocker. This report approves these two specific corrections, not a complete animation or native-rig gate.

Provenance: `repair_jobs.json` contains both correction records; `pelvis_checker_rgb_donors.json` and `torso_checker_rgb_donors.json` identify all donor coordinates; matching correction masks show exactly the RGB edits. The script is `tools/compose_cretan_archer_hidden_repairs.py`.
