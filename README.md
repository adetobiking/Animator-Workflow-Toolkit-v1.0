# Animator Workflow Toolkit - BounceGen (Module 01)

Animation Workflow Toolkit is a modular productivity tool for Autodesk Maya that helps animators automate repetitive animation tasks. 

The first completed module, BounceGen, generates realistic bouncing-ball animations in seconds while allowing users to customize motion, timing, materials, and physics-inspired behaviour. 

The toolkit is designed to grow with additional modules already planned in the interface, including WalkGen, OverlapGen, ArcAssist, FollowThru, and Timing. The goal is to reduce repetitive technical work so animators can focus more on creativity and storytelling.

## Requirements
- Autodesk Maya 2023 or later (Windows)

## Installation
1. Download the latest release from the [Releases page](../../releases).
2. Unzip it.
3. In Maya, open the **Script Editor** (Windows > General Editors > Script Editor).
4. Open a new Python tab, paste in the contents of `install.py`, and run it.
5. Follow the prompt to select the unzipped folder.
6. A **BounceGen** shelf tab appears with **GO** (launch) and **DEL** (uninstall) buttons.

## Usage
1. Click **GO** on the shelf to open the panel — it docks like any native Maya panel (try dragging it next to the Channel Box).
2. Set your global Starting Height, Rebound %, Horizontal Distance, and Arc Axis.
3. Configure each of the 5 ball rows: type, material, color, radius.
4. Click **Generate Bounce** to build the initial set.
5. From here, every change in the panel updates the balls live — no need to click Generate again unless you've cleared the scene.
6. **Clear All Balls** removes everything BounceGen created (balls, shaders, shading groups) so you can start fresh.

NOTE:
1. For live preview to work properly, make sure the ball(s) are no being animated. If they are in motion, you should stop animation before applying changes.
2. Changing the sizes of balls outside the interface is not always effective. Always use the radius slider for desired effect.
3. To change or move the position of any ball, use the outliner. If you move the ball by selecting it directly from the viewport, it will snap back to its default position when was initially generated.
4. If for any reason a function in the UI didn't apply live changes, use the Generate bounce button. It reads the interface settings and apply them accordingly.

## Status
Module 01 (BounceGen) is functional and in active testing. WalkGen, OverlapGen, ArcAssist, and FollowThru (shown as disabled buttons in the header) are planned future modules — not yet implemented.

## Feedback
Found a bug or have a suggestion? Fill this short form at  https://forms.gle/m4DBGvCEm1rNRm898 or reach out directly at adeyemitobikingsley@gmail.com.

## 📄 License & Usage

**BounceGen Maya Toolkit** is provided free of charge for personal, educational, and commercial animation projects. 

> ⚠️ **Important:** This software is **Freeware**, it is **NOT Open Source**. 

While the source code may be visible for transparency and collaborative feedback, all rights remain exclusively with the author. 

### ✅ What You Can Do:
* Download, install, and use the toolkit in any commercial, studio, or freelance production.
* Share the original, completely unmodified release package with others.
* Create incredible animations with it—any creative work you produce belongs entirely to you.

### ❌ What You Cannot Do:
* Modify the code, redistribute altered versions, or claim ownership of the software.
* Copy, republish, or reuse any part of the source code in other software projects.
* Sell, rent, lease, or charge money for access to this toolkit.

For the full legal terms and conditions, please review the accompanying [LICENSE](LICENSE) file in this repository.
