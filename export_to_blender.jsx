/* AE2Blender Bridge 1.0 — place in After Effects/Scripts/ScriptUI Panels, then restart AE. */
(function AE2Blender(thisObj) {
    function isSolid(layer) {
        return layer.source && layer.source.mainSource && (layer.source.mainSource instanceof SolidSource);
    }
    function typeOf(layer) {
        if (layer instanceof CameraLayer) return "camera";
        if (layer.nullLayer) return "null";
        if (isSolid(layer)) return "solid";
        return null;
    }
    function value(group, matchName, time, fallback) {
        var prop = group.property(matchName);
        return prop ? prop.valueAtTime(time, false) : fallback;
    }
    function rgb(color) {
        return [Math.round(color[0] * 255), Math.round(color[1] * 255), Math.round(color[2] * 255)];
    }
    function exportComp() {
        var comp = app.project.activeItem;
        if (!(comp instanceof CompItem)) { alert("Open the composition you want to export."); return; }
        var file = File.saveDialog("Export AE2Blender scene", "AE2Blender JSON:*.json");
        if (!file) return;
        app.beginUndoGroup("Export AE2Blender");
        try {
            var start = Math.round(comp.workAreaStart * comp.frameRate);
            var count = Math.max(1, Math.round(comp.workAreaDuration * comp.frameRate));
            var end = start + count - 1;
            var data = { format: "AE2Blender", version: 1, composition: comp.name, width: comp.width, height: comp.height,
                frameRate: comp.frameRate, frameStart: start, frameEnd: end, layers: [] };
            for (var i = 1; i <= comp.numLayers; i++) {
                var layer = comp.layer(i), kind = typeOf(layer);
                if (!kind || (!layer.threeDLayer && kind !== "camera")) continue;
                var transform = layer.property("ADBE Transform Group");
                var item = { id: layer.index, name: layer.name, type: kind,
                    parentId: layer.parent ? layer.parent.index : null, samples: [] };
                if (kind === "solid") {
                    item.width = layer.width; item.height = layer.height;
                    item.anchor = transform.property("ADBE Anchor Point").value;
                    item.color = rgb(layer.source.mainSource.color);
                }
                if (kind === "camera") item.zoom = layer.property("ADBE Camera Options Group").property("ADBE Camera Zoom").value;
                // Per-frame sampling retains expressions and interpolation over the work area.
                for (var frame = start; frame <= end; frame++) {
                    var time = frame / comp.frameRate;
                    var sample = { frame: frame,
                        position: value(transform, "ADBE Position", time, [0, 0, 0]),
                        orientation: value(transform, "ADBE Orientation", time, [0, 0, 0]),
                        rotation: [value(transform, "ADBE Rotate X", time, 0), value(transform, "ADBE Rotate Y", time, 0),
                            value(transform, "ADBE Rotate Z", time, value(transform, "ADBE Rotation", time, 0))],
                        scale: value(transform, "ADBE Scale", time, [100, 100, 100]) };
                    // Two-node AE cameras derive their direction from this property.
                    if (kind === "camera") sample.pointOfInterest = value(transform, "ADBE Point of Interest", time, null);
                    item.samples.push(sample);
                }
                data.layers.push(item);
            }
            if (!data.layers.length) { alert("No 3D cameras, 3D nulls, or 3D solids were found."); return; }
            if (!file.open("w")) throw new Error("Could not write the selected file.");
            file.write(JSON.stringify(data, null, 2)); file.close();
            alert("Exported " + data.layers.length + " layer(s) to:\n" + file.fsName);
        } catch (error) { alert("AE2Blender export failed:\n" + error.toString()); }
        finally { app.endUndoGroup(); }
    }
    function ui(thisObj) {
        var panel = (thisObj instanceof Panel) ? thisObj : new Window("palette", "AE2Blender", undefined, {resizeable: true});
        panel.orientation = "column"; panel.alignChildren = ["fill", "top"];
        panel.add("statictext", undefined, "Export cameras, 3D nulls, and solids\nfrom the active comp's work area.", {multiline: true});
        var button = panel.add("button", undefined, "Export AE2Blender JSON");
        button.onClick = exportComp;
        panel.onResizing = panel.onResize = function () { this.layout.resize(); };
        return panel;
    }
    var panel = ui(thisObj);
    if (panel instanceof Window) { panel.center(); panel.show(); }
})(this);
