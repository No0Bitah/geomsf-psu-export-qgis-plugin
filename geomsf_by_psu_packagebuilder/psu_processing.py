import os
from qgis.core import *
from qfieldsync.core.cloud_converter import CloudConverter
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from qgis.PyQt.QtCore import QEventLoop, QTimer, QVariant
import processing
import numpy as np
import time
# from create_file_psu import create_file

# ==============================
# EASY SETTINGS (EDIT ONLY THIS)
# ==============================

csv_path, _ = QFileDialog.getOpenFileName(
    None,
    "Select CSV File",
    "",
    "CSV Files (*.csv)"
)

def ask_psu_selection(unique_psu):
    unique_psu_sorted = sorted(unique_psu)

    msg = (
        "Enter PSU number(s) separated by comma\n"
        "Example: 11\n"
        "Example: 11,12,15\n\n"
        "Type ALL to process everything.\n\n"
        f"Available PSU:\n{unique_psu_sorted}"
    )

    text, ok = QInputDialog.getText(
        None,
        "Select PSU",
        msg
    )

    if not ok:
        raise Exception("User cancelled.")

    text = text.strip()

    # If user typed ALL
    if text.upper() == "ALL":
        return unique_psu_sorted

    # Otherwise parse numbers
    try:
        selected = [int(x.strip()) for x in text.split(",")]
    except:
        QMessageBox.critical(None, "Error", "Invalid PSU input.")
        raise Exception("Invalid PSU input.")

    # Validate if PSU exists
    valid_psu = [psu for psu in selected if psu in unique_psu_sorted]

    if not valid_psu:
        QMessageBox.critical(None, "Error", "No valid PSU found.")
        raise Exception("Invalid PSU selection.")

    return valid_psu

if not csv_path:
    raise Exception("No file selected")

# CSV_PATH = r"F:\PSA-GIS-sample\2026 March lfs_City of Iligan_Selected_ssu_R8(RG2).csv"
# CSV_PATH = csv_path
# base_dir = os.path.dirname(CSV_PATH)
base_name = os.path.splitext(os.path.basename(csv_path))[0]


LAYER_NAME = base_name
PSU_FIELD = "PSU_number"
BASE_DIR = os.path.dirname(csv_path)

parts = base_name.split('_')
header = parts[0].split(' ')  # e.g. ['2026', 'April', 'LFS'] or ['2026', 'HSDV']

ACTIVITY_NAME = parts[0]   # '2026 April LFS' or '2026 HSDV'
DOMAIN_NAME   = parts[1]   # 'City of Iligan' or 'Lanao del Norte'
REPLICATE     = parts[4]   # 'R13(RG2)' or 'R47(RG2)'

# MONTH: use the full header block for folder naming (works for both)
MONTH = parts[0]           # '2026 April LFS' or '2026 HSDV' — used in export_qfield folder path


def add_layer(file_path):
    # === Extract filename without extension ===
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    # Layer name = CSV filename
    layer_name = base_name

    # Project filename
    project_filename = base_name + "_csv.qgz"

    # Project save path (same folder as CSV)
    project_path = os.path.join(os.path.dirname(file_path), project_filename)

    # === Create URI for WKT CSV ===
    uri = f"file:///{file_path}?delimiter=,&wktField=WKT&geometryType=Point&crs=EPSG:4326"

    layer = QgsVectorLayer(uri, layer_name, "delimitedtext")

    if not layer.isValid():
        print("Layer failed to load!")
    else:
        # --- Convert CSV layer to memory (editable) ---
        memory_layer = QgsVectorLayer(
            "Point?crs=EPSG:4326",
            layer_name,
            "memory"
        )

        memory_layer_data = memory_layer.dataProvider()

        # Copy fields
        memory_layer_data.addAttributes(layer.fields())
        memory_layer.updateFields()

        # Copy features
        feats = [f for f in layer.getFeatures()]
        memory_layer_data.addFeatures(feats)

        # --- Replace Selected_SSU field type ---
        field_name = "Selected_SSU"
        temp_field = "Selected_SSU_tmp"

        provider = memory_layer.dataProvider()

        # 1️⃣ Add temp Int32 field
        provider.addAttributes([QgsField(temp_field, QVariant.Int)])
        memory_layer.updateFields()

        temp_idx = memory_layer.fields().indexFromName(temp_field)
        orig_idx = memory_layer.fields().indexFromName(field_name)

        # 2️⃣ Copy converted values
        with edit(memory_layer):
            for feat in memory_layer.getFeatures():
                value = feat[field_name]
                int_value = int(value) if value is not None else None
                memory_layer.changeAttributeValue(feat.id(), temp_idx, int_value)

        # 3️⃣ Delete original Boolean field
        provider.deleteAttributes([orig_idx])
        memory_layer.updateFields()

        # 4️⃣ Rename temp field to original name
        new_idx = memory_layer.fields().indexFromName(temp_field)
        provider.renameAttributes({new_idx: field_name})
        memory_layer.updateFields()

        # --- Load into project ---
        QgsProject.instance().clear()
        QgsProject.instance().addMapLayer(memory_layer)

        QgsProject.instance().write(project_path)

        print("Layer loaded successfully!")
        print("Selected_SSU converted to Integer (32-bit).")
        print("Project saved to:", project_path)

def export_psu(layer, unique_psu):

    for psu in unique_psu:

        print(f"\nProcessing PSU {psu}...")

        # --------------------------
        # 1️⃣ EXPORT PSU GPKG
        # --------------------------

        expression = f'"{PSU_FIELD}" = {psu}'
        layer.selectByExpression(expression)

        if layer.selectedFeatureCount() == 0:
            print("No features found.")
            continue

        gpkg_name = f"{ACTIVITY_NAME}_{DOMAIN_NAME}_Selected_ssu_{REPLICATE}_psu_{psu}"
        gpkg_path = os.path.join(BASE_DIR, f"{gpkg_name}.gpkg")

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.onlySelectedFeatures = True
        options.layerName = gpkg_name

        QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            gpkg_path,
            QgsCoordinateTransformContext(),
            options
        )

        layer.removeSelection()
        print("Exported:", gpkg_path)

def create_files(unique_psu):
    for psu in unique_psu:
        project = QgsProject.instance()
        project.clear()

        project.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
        
        TRACKLOG_FILE  = (
            BASE_DIR + r"\\tracklog.gpkg"
        )

        SAMPLE_FILE_1 = (
            BASE_DIR + "\\" +
            f"{ACTIVITY_NAME}_{DOMAIN_NAME}_Selected_ssu_{REPLICATE}_psu_{psu}.gpkg"
        )


        SAMPLE_FILE_2 = (
            BASE_DIR + "\\" + f"{ACTIVITY_NAME}_{DOMAIN_NAME}_Additional SSU or Replacement PSU.gpkg"
        )

        # Styles
        TRACKLOG_FILE_STYLE = os.path.join(BASE_DIR, r"Map Legends\QML-tracklog.qml")
        SAMPLE_FILE_1_STYLE  = os.path.join(BASE_DIR, r"Map Legends\2023 GeoMS Georeferencing Feature Application for Sampling Units- SSU v2.0.qml")
        SAMPLE_FILE_2_STYLE  = os.path.join(BASE_DIR, r"Map Legends\2023 GeoMS Georeferencing Feature Application for Sampling Units-Addtl Replacement SSU v2.0.qml")


        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR)

        project_file = ( 
            BASE_DIR + "\\" +
            f"{ACTIVITY_NAME}_{DOMAIN_NAME}_Selected_ssu_{REPLICATE}_psu_{psu}.qgz"
        )

        # Groups to create
        groups = ["Tracklog", "samples", "Basemap"]

        # --------------------------
        #  CREATE GROUPS
        # --------------------------

        root = project.layerTreeRoot()

        group_objects = {}
        for g in groups:
            group_objects[g] = root.addGroup(g)

        # --------------------------
        # ADD LAYERS TO TRACKLOG
        # --------------------------

        tracklog_file = TRACKLOG_FILE  # path to your tracklog.gpkg
        tracklog_layer = QgsVectorLayer(tracklog_file, "tracklog", "ogr")

        if not tracklog_layer.isValid():
            print("Tracklog layer failed to load!")
        else:
            # APPLY STYLE
            if os.path.exists(TRACKLOG_FILE_STYLE):
                tracklog_layer.loadNamedStyle(TRACKLOG_FILE_STYLE)
                tracklog_layer.triggerRepaint()

            project.addMapLayer(tracklog_layer, False)
            group_objects["Tracklog"].addLayer(tracklog_layer)

        # --------------------------
        # ADD LAYERS TO SAMPLES
        # --------------------------

        samples_files = [
            (SAMPLE_FILE_1, SAMPLE_FILE_1_STYLE),
            (SAMPLE_FILE_2, SAMPLE_FILE_2_STYLE)
        ]

        for sf, style in samples_files:
            # Use QgsVectorLayer to get subLayers safely
            temp_layer = QgsVectorLayer(sf, "temp", "ogr")
            if not temp_layer.isValid():
                print(f"Failed to open {sf}")
                continue
            # # Load all layers inside the GPKG
            for l in temp_layer.dataProvider().subLayers():
                layer_name = l.split('!!::!!')[1]  # extract layer name from subLayers
                layer_path = f"{sf}|layername={layer_name}"
                layer = QgsVectorLayer(layer_path, layer_name, "ogr")
                if layer.isValid():
                    # ADD STYLE
                    if os.path.exists(style):
                        layer.loadNamedStyle(style)
                        layer.triggerRepaint()

                    project.addMapLayer(layer, False)
                    group_objects["samples"].addLayer(layer)
                else:
                    print(f"Layer {layer_name} failed to load from {sf}")

        # --------------------------
        #  ADD GOOGLE SATELLITE TO BASEMAP
        # --------------------------

        # Make sure QMS plugin is installed
        # Layer URI format for QuickMapServices Google Satellite:
        basemap_name = "Google Satellite"
        # basemap_source = (
        #     "type=xyz&zmin=0&zmax=20&url=https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
        # )
        basemap_source = (
            "type=xyz&zmin=0&zmax=20&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D{x}%26y%3D{y}%26z%3D{z}"
        )
        basemap_layer = QgsRasterLayer(basemap_source, basemap_name, "wms")

        if basemap_layer.isValid():
            # Add to project without default root
            QgsProject.instance().addMapLayer(basemap_layer, False)
            # Add to Basemap group
            group_objects["Basemap"].addLayer(basemap_layer)
            print("Google Satellite added successfully")

            # ---- WAIT UNTIL LAYER IS READY ----
            timeout = 8  # seconds
            start_time = time.time()

            while not basemap_layer.isValid():
                QgsApplication.processEvents()
                if time.time() - start_time > timeout:
                    print("Basemap load timeout.")
                    break

            # small buffer delay to allow tile initialization
            QgsApplication.processEvents()
            time.sleep(2)

        else:
            print("Basemap failed to load!")

        # --------------------------
        # SAVE PROJECT
        # --------------------------

        project.write(project_file)
        print("Project saved to:", project_file)

        time.sleep(2)
        export_qfield(project_file,psu)


def export_qfield(project_path,psu):
    export_folder = (BASE_DIR + "\\" + "Package for QField" + "\\" + MONTH + "\\" + f"{DOMAIN_NAME}_{REPLICATE}_PSU{psu}")

    # Ensure export folder exists
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)
        
    # Load project
    project = QgsProject.instance()
    project.read(project_path)

    # Create converter
    converter = CloudConverter(
        project,export_folder
    )

    # Run conversion
    converter.convert()



    print("Export completed.")
    rename_output(export_folder)
    

def rename_output(export_folder):
    print("renaming output file")
    print(export_folder)
    for root, dirs, files in os.walk(export_folder):
        for filename in files:
            if "_cloud" in filename:
                old_path = os.path.join(root, filename)
                new_filename = filename.replace("_cloud", "_qfield")
                new_path = os.path.join(root, new_filename)

                # Avoid overwriting existing files
                if os.path.exists(new_path):
                    print(f"Skipping (already exists): {new_filename}")
                    continue

                os.rename(old_path, new_path)
                print(f"Renamed: {filename}  →  {new_filename}")

    print(f"old: {old_path}")
    print(f"old: {new_path}")
    print("Renaming completed.")

def main():
    add_layer(csv_path)
    # ==============================
    # AUTO EXPORT + PROJECT CREATION
    # ==============================

    project = QgsProject.instance()
    layer = project.mapLayersByName(LAYER_NAME)[0]

    unique_psu = layer.uniqueValues(layer.fields().indexFromName(PSU_FIELD))

    print("Found PSU:", unique_psu)

    # Ask user what PSU to process
    selected_psu = ask_psu_selection(unique_psu)

    print("User selected:", selected_psu)

    my_array = np.array(selected_psu)

    export_psu(layer, my_array)
    create_files(my_array)
    print("--------------------------------")
    print("|    Done with all processing!    |")
    print("--------------------------------")
