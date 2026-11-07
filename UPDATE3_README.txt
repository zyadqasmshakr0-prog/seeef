SEF - Update 3 source patch
==========================

Install
-------
Extract this ZIP directly into the existing F:\sef folder and allow file replacement.

Only these source files are included:
- main.py
- enemies.py
- main_menu.py
- progression.py
- control_editor.py

Do not delete or replace .github/workflows, buildozer.spec, settings.json, assets,
world.py, stage_layout.py, or any other project files. They are not part of this patch.

Changes
-------
1. Android performance:
   - Reuses player/enemy sprite sheets and animation frames.
   - Caches flipped and scaled animation frames.
   - Caches touch-button surfaces.
   - Uses SDL2 SCALED fullscreen mode where supported to avoid a full Python-side
     screen resize on every frame.

2. Arabic:
   - Forces right-to-left bidi direction for Arabic text.
   - Adds a compatible bidi import fallback.

3. Gameplay:
   - Adds 30 strong skeleton enemies along each 35,000-unit stage.
   - Skeletons do not fire arrows.
   - Only guards and the king fire arrows.
   - Enemy health scales more strongly by stage; damage also increases gradually.
   - Coin counter is moved below the health hearts.

4. Shield:
   - First purchase unlocks a 20-second shield.
   - Upgrades raise duration to 30, 40, 50, then 60 seconds.
   - Upgrade prices: 25 to unlock, then 50, 80, 115, and 150 coins.
   - Existing saved shield unlocks are migrated to level 1 (20 seconds).

5. Control editor:
   - Adds - and + buttons to resize the selected control.
   - Keeps the yellow resize handle, drag/move, opacity slider, undo/redo,
     joystick editing, and saved positions.
   - Allows larger buttons and a larger joystick.

Testing
-------
All Python source files passed syntax compilation.
The game could not be launched and an Android APK could not be built in this
environment. Test the APK on the phone before treating the update as final.
