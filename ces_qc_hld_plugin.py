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
            from qgis.core import QgsProject, QgsGeometry
            from qgis.core import QgsProject
# Get the layers by name (update if your layer names differ)
            poles_layer = QgsProject.instance().mapLayersByName('poles')[0]
            route_layer = QgsProject.instance().mapLayersByName('route')[0]
            chambers_layer = QgsProject.instance().mapLayersByName('chambers')[0]
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
#Should be done.
            print(username,f"(Script made it to the end XD)")
            # ... rest of your script ...
            QMessageBox.information(self.iface.mainWindow(), "Success", "QC script completed!")
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Error", str(e))