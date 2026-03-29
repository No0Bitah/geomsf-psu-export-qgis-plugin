# GeoMSF Field Package Builder — QGIS Plugin

A QGIS plugin for the **Philippine Statistics Authority (PSA)** that automates the preparation of QField survey packages from the **2023 Geo-enabled Master Sample Frame (GeoMSF)** SSU CSV files.

---

## Overview

Field survey deployment for PSA household-based surveys requires generating per-PSU GeoPackages, setting up styled QGIS projects, and packaging everything for offline use on tablet devices via **QField**. This plugin automates that entire workflow — reducing manual steps, minimizing human error, and getting field teams ready faster.

This is applicable for LFS and needs some minor updates on files names for CES as of this date of upload due to some files not yet updated for CES.

---

## Features

- 📂 **CSV Loader** — Opens a GeoMSF SSU CSV file and loads it as a spatial point layer (WKT-based, EPSG:4326)
- 🔢 **PSU Selection** — Interactively select one, multiple, or all PSU numbers to process
- 📦 **Per-PSU GeoPackage Export** — Automatically filters and exports a `.gpkg` file per PSU
- 🗺️ **QGIS Project Builder** — Creates a `.qgz` project per PSU with:
  - Tracklog layer (with QML style)
  - Sample SSU layer (with QML style)
  - Additional/Replacement SSU layer (with QML style)
  - Google Satellite basemap (XYZ tiles)
  - Organized layer groups: `Tracklog`, `Samples`, `Basemap`
- 📱 **QField Package Export** — Converts each QGIS project to a QField-ready offline package using `CloudConverter`
- ✏️ **Auto-Rename** — Renames `_cloud` suffixed files to `_qfield` for clarity

---

## Requirements

| Requirement | Version |
|---|---|
| QGIS | 3.x (LTR recommended) |
| Python | 3.x (bundled with QGIS) |
| QFieldSync Plugin | Latest |
| NumPy | Bundled with QGIS |

> ⚠️ The **QFieldSync** plugin must be installed and enabled in QGIS before using this plugin.

---

## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/No0Bitah/geomsf-psu-export-qgis-plugin.git
   ```

2. In your QGIS:
   - Click `Plugins  --> Manage and install plugins --> Install from ZIP`
   - Select the Zip file from the cloned folder
   - Click `Install Plugin`
   - Check in `Installed`

3. Enable the plugin via **Plugins → Manage and Install Plugins → Installed**.

4. Plugin Icon cna be seen in the Toolbar or in the plugins
---

## Folder Structure Expected

Before running the plugin, ensure the following files and folders exist alongside your CSV:

```
<BASE_DIR>/
├── {Activity Name}_{Domain Name}_Selected SSU_{ReplicateNumber}.csv NOTE! CSV (Comma delimited)
├── tracklog.gpkg
├── {Activity Name}_{Domain Name}_Additional SSU or Replacement PSU.gpkg
└── Map Legends/
    ├── QML-tracklog.qml
    ├── 2023 GeoMS Georeferencing Feature Application for Sampling Units- SSU v2.0.qml
    └── 2023 GeoMS Georeferencing Feature Application for Sampling Units-Addtl Replacement SSU v2.0.qml
```

---

## CSV Filename Convention

The plugin parses metadata directly from the CSV filename. Follow this naming format:

```
<MONTH>_<DOMAIN>_Selected_ssu_R<REPLICATE NUMBER>.csv
```

**Example:**
```
2026 March lfs_City of Iligan_Selected_ssu_R8.csv
```

| Segment | Parsed Value |
|---|---|
| `2026 March lfs` | ACTIVITY / MONTH |
| `City of Iligan` | DOMAIN NAME |
| `R8` | REPLICATE |

---

## Output Structure

After processing, the plugin generates:

```
<BASE_DIR>/
├── <ACTIVITY>_<DOMAIN>_Selected_ssu_<REPLICATE>_psu_<N>.gpkg     ← per-PSU GeoPackage
├── <ACTIVITY>_<DOMAIN>_Selected_ssu_<REPLICATE>_psu_<N>.qgz      ← per-PSU QGIS project
└── Package for QField/
    └── <MONTH> <DOMAIN>/
        └── <DOMAIN>_<REPLICATE>_PSU<N>/                          ← QField package per PSU
            └── *.gpkg  (renamed from _cloud to _qfield)
```

---

## Usage

1. Open QGIS and activate the plugin.
2. Click the plugin toolbar button or navigate to **Plugins → GeoMSF by psu Package Builder**.
3. Select your SSU CSV file when prompted.
4. Choose PSU numbers to process (or type `ALL`).
5. Wait for the plugin to complete — output files will be saved alongside the CSV.

---

## Background

This plugin supports the **Implementation of the 2023 GeoMS Georeferencing Feature Application for Sampling Units**, developed by the Census Planning and Coordination Division (CPCD) of the National Censuses Service (NCS), PSA. It addresses recurring field issues with locating sample households by leveraging the geospatial (WKT/XY) information already embedded in the GeoMSF.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/No0Bitah/geomsf-psu-export-qgis-plugin/issues)
- **Discussions**: [GitHub Discussions](https://github.com/No0Bitah/geomsf-psu-export-qgis-plugin/discussions)
- **Email**: jomari.daison@gmail.com

---

**Made with ❤️ by [No0Bitah](https://github.com/No0Bitah)**