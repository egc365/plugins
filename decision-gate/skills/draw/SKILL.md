---
name: draw
description: "Natural-language to verified 3D scenes. Takes a goal ('an apple','a lab bench with beakers'), retrieves or generates bpy script, executes headless, verifies the scene, exports PNG/FBX/GLTF. Every render is training data. Use for /draw, slide art, 3D assets, or 'make me a scene of X'."
---

# Draw

Turns words into verified 3D. Never claims an object exists without probing
the scene. Never trusts exit codes.

## Loop
1. PARSE: goal -> object list, materials, layout constraints
2. RETRIEVE: nearest proven recipe from the corpus (idf char-ngram);
   abstain to generation if best score < threshold
3. GENERATE or RECALL: known shape = corpus script (possibly composed);
   novel = compose from verified primitives (sphere/box/cyl/curve+modifiers)
4. EXECUTE: headless blender, fresh temp blend, capture DGSTATE
5. VERIFY: evaluator checks against the goal's expect block (objects exist,
   dims within tol, material assigned) - NOT exit codes
6. EXPORT: PNG (workbench/eevee), optional FBX/GLTF for slides
7. RECORD: pair into the corpus via ExampleStore (label from checks)

## Fail state
Any verify miss => retry with repaired script (max 2), then return the
failure evidence honestly. A render without a passing verify is labeled
'unverified draft', never 'done'.

## Escalation
Composition misses and novel geometry => the d8 text layer / frontier.
The bot ships narrow and verified; widens only with corpus evidence.
