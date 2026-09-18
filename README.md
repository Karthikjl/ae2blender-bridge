# AE2Blender Bridge

Transfer animated 3D cameras, nulls, and solid layers from Adobe After Effects to Blender using a JSON file.

## What is included

- `export_to_blender.jsx` — After Effects ScriptUI panel and exporter.
- `ae_bridge.py` — Blender add-on and JSON importer.
- `export.json` — example export file (optional; it is not required by the add-on).

The bridge transfers layer hierarchy, position, orientation, rotation, scale, solid dimensions, anchor points, colors, camera zoom, camera point-of-interest data, frame rate, and animation frames.

## Requirements

- Adobe After Effects with 3D layers/camera support.
- Blender 3.0 or newer. Blender 4.x and 5.x are recommended.

## After Effects installation

1. Copy `export_to_blender.jsx` to the After Effects **Scripts/ScriptUI Panels** folder.
2. In After Effects, open **Edit > Preferences > Scripting & Expressions**.
3. Enable **Allow Scripts to Write Files and Access Network**.
4. Restart After Effects.
5. Open a composition and choose **Window > AE2Blender**.

## Export from After Effects

1. Open the composition containing the tracked camera, nulls, or solids.
2. Set the composition work area to the range you want to transfer.
3. Click **Export AE2Blender JSON** in the AE2Blender panel.
4. Choose a filename and location for the `.json` file.

The exporter includes 3D cameras, 3D nulls, and solid layers. It samples every frame in the work area, which preserves expressions and camera-tracking animation. 2D layers and unsupported layer types are skipped.

## Blender installation

1. Open Blender and choose **Edit > Preferences > Add-ons**.
2. Click **Install…**.
3. Select `ae_bridge.py`.
4. Enable **AE2Blender Bridge**.

The add-on adds an **AE2Blender** tab to the 3D View sidebar.

## Import into Blender

1. Open a 3D View and press `N` to open the sidebar.
2. Select the **AE2Blender** tab.
3. Click **Import AE2Blender JSON**.
4. Select the JSON exported from After Effects.
5. Set the pixel scale if needed. The default is `1 AE pixel = 0.01 Blender units`.
6. Press `Numpad 0` to view through the imported camera.

Imported objects are placed in an `AE2Blender Import` collection. The imported camera is automatically assigned as Blender's active scene camera.

## Updating the add-on

After replacing `ae_bridge.py` with a newer version, disable and re-enable the add-on or restart Blender. Delete the old `AE2Blender Import` collection before importing the updated JSON again.

## Troubleshooting

### The camera view does not match After Effects

- Make sure you are viewing through the camera with `Numpad 0`, not using **User Perspective**.
- Delete the previous imported collection and import again.
- Re-export the JSON after changing the AE camera or work area.
- Confirm that the AE composition resolution and frame rate are correct.

### The add-on does not appear

- Install the individual `ae_bridge.py` file, not the whole repository folder.
- Confirm the add-on is enabled in Blender Preferences.
- Restart Blender after updating the file.

### The AE panel does not appear

- Place the JSX file specifically in the **Scripts/ScriptUI Panels** folder.
- Restart After Effects.
- Confirm that script file access is enabled in Preferences.

## Coordinate and camera conversion

The importer follows the AE-to-Blender camera convention: AE position `X/Y/Z` becomes Blender `X/Z/-Y`; camera X-axis correction, YZX rotation order, quaternion keys, and horizontal field of view from AE zoom are applied during import.

## License

This project is licensed under the **MIT License**. See the [`LICENSE`](LICENSE) file for the complete license text.

You may use, copy, modify, merge, publish, distribute, sublicense, and sell copies of this software, provided that the copyright notice and permission notice are included in all copies or substantial portions of the software.
