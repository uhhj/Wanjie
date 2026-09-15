# Roman Guard heavy slash candidate

Built-in image_gen generated `heavy_slash_motion_reference_v1.png`; exact prompt in `reference_prompt.txt`. Generated poses guide timing/load only, not formal pixels or design. The sword depiction/projection and rear heel lift in the reference are not copied into the frozen art.

Native changes: slight rear preload, raised sword, pelvis/torso drive, forward/down slash and controlled recovery. Both knees now flex forward; reduced hip descent avoids mirrored deep squat. This version keeps both soles planted instead of reproducing the reference heel lift. Hit method event occurs once at 0.54s; duration 1.32s. Other four animations, skeleton, knee plate, materials and parts are unchanged.

Review `heavy_slash_256.gif`, `heavy_slash_192.gif`, and `reference_comparison.png` at native scale. Shoulder armour compression remains; this is a new visual candidate, not user-approved final motion. `review.json` and `headless_tests.json` contain current checks. Earlier global delivery evidence predates this attack revision.

Rebuild: tools/author_roman_heavy_slash.py; Godot --headless --script scripts/build/update_roman_attack_keys.gd; tools/install_roman_heavy_slash.py. Capture with Godot GPU scripts/tests/capture_roman_heavy_slash.gd, then tools/review_roman_heavy_slash.py. Test scripts/tests/test_native_rig.gd.

V2: higher overhead/back preparation, larger hip transfer, fast cut and slower recovery. Cape motion starts earlier to preserve the raised-arm silhouette. Review versioned heavy_slash_v2_256/192.gif. Headless tests and native planted-foot drift passed. Original rig structure, parts and four other animations unchanged.
