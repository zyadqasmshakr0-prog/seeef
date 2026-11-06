SEF - The Adventurer | Update 2 source patch

Apply this patch by extracting its contents directly into your existing F:\sef folder and allowing overwrite of matching files.
Do not delete or replace your existing .github/workflows folder or buildozer.spec; this patch does not include them.

Included changes:
- Arabic shaping and Arabic HUD/touch labels.
- Android fullscreen presentation that scales the 1280x720 game canvas to the native display bounds.
- Persistent progress and currency in progress.json (stored in the app's writable preferences folder).
- Stage unlocks: stage 1 starts open; defeating a stage king and reaching the gate unlocks the next stage.
- Rewards: ordinary enemies 2 coins, royal guards 4, kings 6, stage completion 6.
- Armory: sword damage, shield, spear, extra jumps, and berserk upgrades.
- Shield lasts 60 seconds; its cooldown is 120 seconds.
- Ultimate animation is faster and its cooldown is 120 seconds.
- Guards and kings fire arrows; a sword attack or shield blocks them.
- Increased enemy health/damage and larger king presentation.
- Corrected enemy and king placement to use the current stage gate/length.

Controls for newly unlocked skills:
- U: activate shield.
- I: throw spear.
- On Android, use the on-screen Shield and Spear buttons.

Verification:
- All Python source files passed Python syntax compilation.
- Progress save/load and stage-unlock logic passed a small isolated test.
- Full Pygame gameplay/build could not be run in this environment because Pygame is not installed here. Build and test on your normal GitHub Actions Android workflow before installing the APK.

No backup copies are included or created by this patch.
