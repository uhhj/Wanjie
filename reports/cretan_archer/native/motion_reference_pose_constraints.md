# New motion reference constraints — independent analysis

Inputs are the user's new Walk, Attack, Death strips. They are motion references only, not production pixels or identity authority. This is pose planning, not rendered visual PASS.

## Attack

Readable phases: relaxed bow grip; near hand reaches above/back to quiver; hand brings the arrow forward; nock joins string; far bow arm extends; draw hand anchors beside cheek/jaw while its elbow moves back/outward; arrow releases; draw hand follows through briefly; controlled recovery. During aim, shaft, nock and draw hand must share a coherent line, and bow hand must remain attached to the grip. The previous chest-level draw does not meet this reference.

The current near-arm skeleton shoulder (440,425), elbow (382,653), wrist (388,789) has segment lengths about 235.26/136.13. Face-directed wrist targets (530,320) or (535,300) produce backward-branch elbow positions around (480,193) or (454,190), above the head, and the other branch is forward at x~662. Changing key angles alone cannot produce the reference's elbow-back face draw with that projected length split.

Native-only deformation-control candidate for testing: shoulder (440,448), elbow control (382,600), wrist unchanged (388,789), giving 162.69/189.10. Wrist target (520,345) then solves the backward branch at elbow (331.81,326.50); (525,340) gives (336.74,322.28). Rotate the hand so its actual nock/socket offset lifts the grip toward the cheek around (550,300). Keep the original zero-degree pixel placement through rest offsets. Blend lower bare upper-arm pixels approximately y575–650 between upper and forearm controls, while the upper sleeve cap remains mainly torso-weighted. This is a deformation control proposal requiring GPU review, not an assertion that the old anatomy was wrong or a request to repaint/re-split PNGs. Do not move the shoulder pivot down to the armpit purely to satisfy a solver.

## Death

Reference order is chest reaction, loss of leg support, knee contact, torso tipping forward, head/chest contact, then settle. A large whole-body roll starting from straight standing legs recreates the earlier plank fall and misses the reference.

Maintain near-zero whole-body roll through the kneeling phase. A source-canvas seed with ground around y1450 is pelvis down about 330–350, hips around (455,1180)/(563,1180), knees around (613,1398)/(725,1398), and ankles folded back around (366,1398)/(488,1398). These nearly preserve the existing 269/272 thigh and 247/237 shin lengths. Aim toes backward with local foot compensation, then use the actual opaque-mesh floor solver for exact ground contact. Hold a knee-contact key briefly before pitching torso/pelvis forward. Final overall orientation should place the head to screen-right near the ground with knees/legs folded behind; local hip/knee compensation is necessary while overall orientation reaches approximately +70–90 degrees. Bow can remain hand-following; any visual bow release should occur after ground contact without introducing physics/combat logic.

## Walk

The new strip reinforces opposite leg phases, clear rear-foot lift before passing, heel-first contact, foot/shin directional coupling and gentle free-arm counter-swing. Existing support-foot world tracking remains the engineering authority. Neither pixel similarity nor rigidly copying the strip's eight images is an appropriate gate.

All numerical seeds above are unapproved key/skinning proposals. Only new actual Godot GPU captures at 256px and 192px can establish the final movement verdict.
