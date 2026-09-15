from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
import os.path

class CESQCPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')  # Optional icon
        self.action = QAction(QIcon(icon_path), "Run CES QC", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&CES QC", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&CES QC", self.action)

    def run(self):
        # Paste your entire script code here!
        # (The improved version I gave you last time)
        # It will run when the toolbar button or menu item is clicked
        try:
            # Your code starts here...
            import processing
            import getpass
            import os
            from qgis.core import QgsProject, QgsGeometry, QgsFeatureRequest

# Look up a layer by name, ignoring case, with a clear error if it's missing
            def get_layer(layer_name):
                for layer in QgsProject.instance().mapLayers().values():
                    if layer.name().lower() == layer_name.lower():
                        return layer
                raise Exception(f" Whhhhhhhhoooopppps '{layer_name}' layer not found. Please make sure it is loaded in the project and named correctly.")

# Get the layers by name (case-insensitive; update if your layer names differ)
            poles_layer = get_layer('poles')
            route_layer = get_layer('route')
            chambers_layer = get_layer('chambers')
            demand_points_layer = get_layer('demand_points')
            drops_layer = get_layer('fibre_cable')
            username = getpass.getuser()
# Step 1: Fix geometries on the routes (line) layer to avoid errors
            fix_result = processing.run("native:fixgeometries", {
                'INPUT': route_layer,
                'OUTPUT': 'memory:'  # Explicitly memory-based temporary layer
            })
            fixed_routes = fix_result['OUTPUT']  # This is a QgsVectorLayer in memory
# Optional: give it a clear name (doesn't appear in Layers panel unless added)
            fixed_routes.setName('Fixed Routes (memory)')
            print(username,f"(Fixed the route geometries)")
# Step 2: Extract poles that are disjoint (do not intersect/touch) the fixed routes
            temp_poles = processing.runAndLoadResults("native:extractbylocation", {
                'INPUT': poles_layer,
                'PREDICATE': [2],  # 2 corresponds to 'disjoint' (no spatial relationship)
                'INTERSECT': fixed_routes,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
# Get the ID of the newly created extracted layer
            extracted_layer_id = temp_poles['OUTPUT']

# Retrieve the layer object and rename it
            extracted_layer = QgsProject.instance().mapLayer(extracted_layer_id)
            extracted_layer.setName('Diconnected_Poles')  # Change this to your preferred name
            print(username,f"(Poles are done)")
# Step 3: Extract chambers that are touching (are touching) the fixed routes
            temp_chambers = processing.run("native:extractbylocation", {
                'INPUT': chambers_layer,
                'PREDICATE': [4],  # 4 corresponds to 'touch' (touch at boundaries but interiors do not intersect)
                'INTERSECT': fixed_routes,
                'OUTPUT': 'memory:'
            })
# The result is now stored in a variable as a QgsVectorLayer (not added to the project)
            temp_chambers_test = temp_chambers['OUTPUT']
# Give it a meaningful name (useful if you later add it or inspect it)
            temp_chambers_test.setName('Temp_Chambers (memory)')

# Example: check how many features were found
            feature_count = temp_chambers_test.featureCount()
            print(username,f"(Temp chambers have been made and stord in the memory)")
# Step 3: Extract chambers that are touching (touch at boundaries but interiors do not intersect) the fixed routes
            disconnected_chambers = processing.runAndLoadResults("native:extractbylocation", {
                'INPUT': chambers_layer,
                'PREDICATE': [2],  # 2 corresponds to 'disjoint' (no spatial relationship)
                'INTERSECT': temp_chambers_test,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })

# Get the ID of the newly created extracted layer
            extracted_layer_id = disconnected_chambers['OUTPUT']

# Retrieve the layer object and rename it
            extracted_layer = QgsProject.instance().mapLayer(extracted_layer_id)
            extracted_layer.setName('Disconnected_Chambers')  # Change this to your preferred name

            print(username,f"(Diconnected Chambers are Done)")

# Step 4: Fix geometries on the drops (fibre cable, pole-to-demand-point) layer
            fix_drops_result = processing.run("native:fixgeometries", {
                'INPUT': drops_layer,
                'OUTPUT': 'memory:'
            })
            fixed_drops = fix_drops_result['OUTPUT']
            fixed_drops.setName('Fixed Drops (memory)')
            print(username,f"(Fixed the drop cable geometries)")

# Step 5: Extract demand points that are disjoint (not served by a drop cable) from the fixed drops
            temp_demand_points = processing.runAndLoadResults("native:extractbylocation", {
                'INPUT': demand_points_layer,
                'PREDICATE': [2],  # 2 corresponds to 'disjoint' (no spatial relationship)
                'INTERSECT': fixed_drops,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })
# Get the ID of the newly created extracted layer
            extracted_layer_id = temp_demand_points['OUTPUT']

# Retrieve the layer object and rename it
            extracted_layer = QgsProject.instance().mapLayer(extracted_layer_id)
            extracted_layer.setName('Disconnected_Demand_Points')  # Change this to your preferred name
            print(username,f"(Demand points are done)")

# Step 6: Flag duplicate geometries (same coordinates digitized twice) in each layer
            def extract_duplicate_features(source_layer, result_name):
                seen_geometries = {}
                for feature in source_layer.getFeatures():
                    wkt_key = feature.geometry().asWkt(13)  # rounded WKT so identical coords always match
                    seen_geometries.setdefault(wkt_key, []).append(feature.id())
                duplicate_fids = [fid for fids in seen_geometries.values() if len(fids) > 1 for fid in fids]
                duplicate_layer = source_layer.materialize(QgsFeatureRequest().setFilterFids(duplicate_fids))
                duplicate_layer.setName(result_name)
                QgsProject.instance().addMapLayer(duplicate_layer)
                return len(duplicate_fids)

            duplicate_poles_count = extract_duplicate_features(poles_layer, 'Duplicate_Poles')
            print(username, f"(Duplicate poles found: {duplicate_poles_count})")

            duplicate_routes_count = extract_duplicate_features(fixed_routes, 'Duplicate_Routes')
            print(username, f"(Duplicate routes found: {duplicate_routes_count})")

            duplicate_chambers_count = extract_duplicate_features(chambers_layer, 'Duplicate_Chambers')
            print(username, f"(Duplicate chambers found: {duplicate_chambers_count})")

            duplicate_demand_points_count = extract_duplicate_features(demand_points_layer, 'Duplicate_Demand_Points')
            print(username, f"(Duplicate demand points found: {duplicate_demand_points_count})")

#Should be done.
            print(username,f"(Script made it to the end XD)")
            # ... rest of your script ...
            QMessageBox.information(self.iface.mainWindow(), "Success", "QC script completed!")
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Error", str(e))
