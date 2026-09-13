# Archer native rig reuse: inspected implementation path

This is a read-only architecture inspection and implementation plan. No Archer Rig has been built or approved by this note. Formal parts and motion/recomposition gates must pass before construction.

## Existing working path

- `tools/build_native_rig_data.py` writes the shared `scenes/rigs/human_medium_rig_v1.tscn`, shared rig JSON, Roman animation JSON, Roman local meshes and masks. **Do not run it for Archer**: its entry point overwrites frozen Roman/shared outputs.
- `scripts/build/build_native_scenes.gd` instantiates the generic Skeleton2D, clears `scene_file_path`, attaches same-canvas textures with `Sprite2D.centered=false` and sprite local position `-source_pivot`, adds AnimationPlayer/method tracks, then packs an owned scene.
- That scene builder is Roman-specific: it skips the near shin sprite, installs Roman knee/shoulder/ankle meshes, keys helmet/death blood, loads Roman textures and writes Roman resource paths. Copy the reusable builder mechanics into an Archer-specific builder; do not run or patch the Roman entry point.
- `scripts/rig/rig_debug.gd` is already generic. It locates `VisualRoot/Skeleton2D`, traverses Bone2D nodes and recognizes socket names dynamically; it can be reused unchanged.

## Smallest safe implementation after assets pass

1. Produce unit-specific `resources/cretan_archer_rig_v1.json` with approved Archer source pivots, parent paths, local offsets, bone lengths, ground origin, body height and part attachments. Preserve the shared `resources/human_medium_rig_v1.json` bytes.
2. Instantiate the existing generic skeleton in the Archer scene builder. Override each cloned Bone2D `position`, `rest`, `length` and `bone_angle` from the unit data. Updating both position and rest is essential for skinning/reset consistency. Reuse the existing 23 names/hierarchy; dormant sword/shield socket nodes can remain unused.
3. Add `bow_socket` beneath `hand_far`, `arrow_socket` beneath `hand_near`, and `quiver_socket` beneath `torso` (26 total bones if all three are Bone2D). Attach bow to the bow-named socket, never shield_socket. Bind cloak to the existing generic cape branch; no need to rename shared hierarchy for the texture name.
4. Attach same-canvas part textures using `sprite.position = -source_pivot_of_attachment_bone`, centered=false. Skeleton position is `-unit_ground_origin`. This restores source coordinates at rest after the Archer-specific bone offsets are applied. Do not reuse Roman ground origin `(530,1460)` or its dimensions by assumption.
5. Use an Archer-specific centralized draw-order table. Preserve the corrected garment ownership: pelvis owns cloth hem and central tail; limbs own sleeves/skin; completed hidden body caps remain underneath. No automatic inclusion of Roman knee plate or Roman mode-specific shoe meshes.
6. Generate only five Archer animation resources. Reuse the continuous value-track builder and per-bone explicit rest/reset keys. Keep all output paths Archer-specific. The Roman key data and walk trajectory contain accepted soldier-specific hip/shoulder offsets, sole shapes and compensation; copying these values would not establish Archer gait reuse.
7. Add a separate Archer event relay with `attack_release` and `_event_attack_release`. Put exactly one method key in attack_01. The Roman relay only has attack_hit; changing it is unnecessary. Key arrow visibility and string drawing/release geometry explicitly. Equipment must retain actual local grip attachment through the release.
8. Reuse runtime root-motion bookkeeping in an Archer unit script, parameterized by its own stride/resource. Keep cycle wrap handling, pause behavior, attack/hit return-to-idle and death hold. The existing Roman rest_pose contains Roman art-node visibility switches; omit those in Archer.

## Tests/captures worth adapting

`scripts/tests/test_native_rig.gd` provides working checks for engine version, animation track NodePaths, exactly-one method event, state transitions, material foot contacts, two-cycle root motion and pause behavior. Adapt the method/weapon/node counts and load Archer unit paths. Do not carry over its Roman Polygon2D count, sword coordinate, helmet or blood assumptions.

Its planted-foot test uses a hardcoded Roman `SOLE` profile. Measure each approved Archer shoe's lower material points and use Archer phase support intervals. Check actual world coordinates at both 256/192px, including runtime loop boundaries; a visually matched walk-reference frame is not a substitute.

`scripts/tests/capture_native_animations.gd` uses real Godot SubViewport GPU capture and manual AnimationPlayer seeking. Reuse this mechanism with Archer scene/data/output paths, a ground origin from its own source bbox, and 256/192px. Retain world motion/ground markers for the walk-reference comparison; do not run the Roman capture entry point because it writes accepted Roman reports.

No additional plugin or retargeting framework is needed. The substantial per-unit work is art completion/ownership, source-pivot calibration, motion key values and contacts; the native hierarchy, scene packing, track creation, rendering and test strategy already exist.
