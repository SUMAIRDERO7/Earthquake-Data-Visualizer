# 🌍 Earthquake Data Visualizer

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python\&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit\&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Geospatial-77B829)
![Pytest](https://img.shields.io/badge/Tests-66%20Passing-brightgreen?logo=pytest)
![License](https://img.shields.io/badge/License-MIT-green)

**Earthquake Data Visualizer** is an interactive geospatial dashboard for exploring earthquake activity using public USGS earthquake data.

The application follows a **live-first data strategy**: it attempts to retrieve the latest USGS GeoJSON earthquake feed and automatically falls back to a realistic, geography-aware cached dataset when the live service is unavailable.

The dashboard combines **interactive mapping, magnitude filtering, frequency analysis, risk-zone aggregation, significant-event detection, searchable earthquake records, and CSV export** into a map-first monitoring experience.

---

## 📌 Table of Contents

* [Overview](#-overview)
* [Problem Statement](#-problem-statement)
* [Key Features](#-key-features)
* [Dashboard](#-dashboard)
* [Data Pipeline](#-data-pipeline)
* [Architecture](#-architecture)
* [Technology Stack](#-technology-stack)
* [Project Structure](#-project-structure)
* [Data Source & Fallback Strategy](#-data-source--fallback-strategy)
* [Analytical Methods](#-analytical-methods)
* [Testing](#-testing)
* [Installation](#-installation)
* [Usage](#-usage)
* [Deployment](#-deployment)
* [Design Decisions](#-design-decisions)
* [Limitations](#-limitations)
* [Future Roadmap](#-future-roadmap)
* [Contributing](#-contributing)
* [License](#-license)
* [Author](#-author)

---

## 🔎 Overview

Earthquake datasets contain valuable information such as:

* Magnitude
* Epicenter coordinates
* Depth
* Location
* Timestamp
* Event frequency

However, raw earthquake records are difficult to interpret without visualization and aggregation.

This project transforms earthquake events into an interactive monitoring dashboard where users can quickly answer questions such as:

* Where are earthquakes occurring?
* Which regions have the highest activity?
* How frequently are earthquakes occurring?
* What magnitude range dominates the current dataset?
* Are there significant M6.0+ events?
* How does earthquake activity change over time?
* Which geographical zones have the highest event concentration?

---

## 🎯 Problem Statement

Raw earthquake data is often presented as tables or machine-readable feeds, making it difficult to identify geographical patterns and temporal trends.

**Earthquake Data Visualizer** addresses this problem by converting earthquake records into an interactive visual analytics system.

The application combines:

> **Live data → Validation → Analysis → Geospatial aggregation → Interactive visualization**

The result is a map-first dashboard designed for fast exploration of seismic activity.

---

## ✨ Key Features

### 🌐 Live-First USGS Data

* Attempts the real USGS earthquake GeoJSON feed.
* Automatically falls back when the live service is unavailable.
* Clearly identifies whether the application is using:

  * 🟢 Live USGS data
  * 🟠 Cached fallback data
* Never silently presents synthetic data as live data.

### 🗺️ Interactive Folium Map

The map is the primary interface of the dashboard.

It provides:

* Magnitude-based marker colors
* Magnitude-based marker sizes
* Interactive popups
* Earthquake location information
* Depth information
* Event timestamps
* Toggleable map layers
* Magnitude-weighted heatmap
* Risk-zone overlays

### 📊 Magnitude Filtering

Users can dynamically filter earthquakes using a magnitude range slider.

The selected range affects:

* Map markers
* Heatmap
* Statistics
* Frequency trends
* Magnitude distribution
* Risk zones
* Data table

### 📅 Daily Frequency Analysis

The dashboard calculates earthquake activity by day and provides:

* Daily earthquake counts
* Average magnitude per day
* Temporal activity trends

### ⚠️ Significant Event Detection

The system automatically identifies earthquakes with:

**Magnitude ≥ 6.0**

These events are highlighted prominently so users don't need to manually inspect hundreds of markers.

### 📍 Place Search

Users can search earthquake events by place name.

For example:

```text
Alaska
Japan
Chile
California
Indonesia
Turkey
```

The search applies across the dashboard's filtered dataset.

### 🧭 Grid-Based Risk Zones

The application divides geographical space into grid cells and aggregates earthquake activity.

Each zone can provide:

* Event count
* Maximum magnitude
* Geographic concentration

This provides a simple and explainable way to identify areas experiencing higher earthquake activity.

> **Important:** These zones represent recent earthquake activity, not scientifically validated seismic hazard predictions.

### 📋 Sortable Earthquake Table

Users can inspect individual earthquake records through a sortable data table containing information such as:

* Location
* Magnitude
* Depth
* Latitude
* Longitude
* Timestamp

### 📥 CSV Export

Filtered earthquake records can be exported as CSV for:

* Further analysis
* Data science workflows
* Reporting
* External visualization
* Research experiments

### 🎨 Map-First Dashboard

The interface follows a dedicated **Seismic Monitor** design:

```text
┌──────────────────────────────────────────────┐
│              SEISMIC MONITOR                 │
├──────────────────────────────────────────────┤
│ KPI  │ KPI │ KPI │ KPI │ Data Source        │
├──────────────────────────────────────────────┤
│                                              │
│              INTERACTIVE MAP                 │
│                                              │
│                                              │
├──────────────────────────────────────────────┤
│ Frequency │ Distribution │ Risk Zones │ Data │
└──────────────────────────────────────────────┘
```

The map remains the primary interface while analytics support geographical interpretation.

---

## 🖥️ Dashboard

The dashboard is organized around four main analytical areas:

### 1. Overview

Provides high-level earthquake statistics including:

* Total events
* Average magnitude
* Maximum magnitude
* Significant events
* Current data source

### 2. Frequency

Displays day-by-day earthquake activity and average magnitude trends.

### 3. Magnitude Distribution

Shows how earthquake magnitudes are distributed across the selected dataset.

### 4. Risk Zones

Ranks geographical grid cells according to earthquake activity.

### 5. Earthquake Data

Provides a detailed sortable table with CSV export functionality.

---

## 🔄 Data Pipeline

```text
                    ┌───────────────────────┐
                    │     USGS GeoJSON      │
                    │      Live Feed        │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    USGS Client        │
                    │ Live-First Strategy   │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             Live Dataset           Cached Snapshot
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │ Earthquake Analysis   │
                    ├───────────────────────┤
                    │ • Filtering           │
                    │ • Frequency           │
                    │ • Distribution        │
                    │ • Significant Events  │
                    │ • Risk Zones          │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Map Builder        │
                    ├───────────────────────┤
                    │ • Markers             │
                    │ • Heatmap             │
                    │ • Risk Zones          │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Seismic Monitor UI   │
                    │      Streamlit        │
                    └───────────────────────┘
```

---

## 🏗️ Architecture

The project follows a modular architecture where each component has a focused responsibility.

```text
earthquake-data-visualizer/
│
├── Data Layer
│   ├── usgs_client.py
│   └── cached_snapshot.py
│
├── Analysis Layer
│   └── earthquake_analysis.py
│
├── Visualization Layer
│   └── map_builder.py
│
├── Service Layer
│   └── visualizer_service.py
│
└── Presentation Layer
    ├── app.py
    └── main.py
```

### Core Components

#### `usgs_client.py`

Responsible for:

* Communicating with the USGS API
* Parsing GeoJSON
* Normalizing earthquake records
* Handling network failures
* Triggering fallback behavior

#### `cached_snapshot.py`

Generates a realistic offline dataset when the live service is unavailable.

The generator supports an explicit `now` parameter to make generated timestamps deterministic during testing.

#### `earthquake_analysis.py`

Contains analytical functionality including:

* Magnitude filtering
* Place-name searching
* Daily frequency analysis
* Magnitude distribution
* Significant-event detection
* Risk-zone aggregation

#### `map_builder.py`

Responsible for constructing the Folium visualization:

* Earthquake markers
* Heatmap layer
* Risk-zone layer
* Interactive popups
* Layer controls

#### `visualizer_service.py`

Acts as the main orchestration layer.

Both the CLI and Streamlit application use the same service instead of duplicating business logic.

---

## 🧰 Technology Stack

| Category          | Technology       |
| ----------------- | ---------------- |
| Language          | Python 3.12      |
| Dashboard         | Streamlit        |
| Mapping           | Folium           |
| Streamlit Mapping | streamlit-folium |
| Data Processing   | Pandas           |
| HTTP Client       | Requests         |
| Testing           | Pytest           |
| Data Format       | GeoJSON / CSV    |
| Version Control   | Git / GitHub     |

---

## 📁 Project Structure

```text
earthquake-data-visualizer/
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── exceptions.py
│   ├── cached_snapshot.py
│   ├── usgs_client.py
│   ├── earthquake_analysis.py
│   ├── map_builder.py
│   └── visualizer_service.py
│
├── tests/
│   ├── __init__.py
│   ├── test_cached_snapshot.py
│   ├── test_usgs_client.py
│   ├── test_earthquake_analysis.py
│   ├── test_map_builder.py
│   └── test_visualizer_service.py
│
├── data/
│   └── generated files and HTML maps
│
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

## 🌎 Data Source & Fallback Strategy

The primary data source is the public earthquake feed provided by the **United States Geological Survey (USGS)**.

The application follows a **live-first architecture**:

```text
Try Live USGS Feed
        │
        ├── Success ──► Use Live Data
        │
        └── Failure
                │
                ▼
        Generate Fallback Dataset
                │
                ▼
        Clearly Label Cached Data
```

This design ensures the application remains functional even when:

* The network is unavailable
* The API is temporarily unreachable
* A deployment environment restricts outbound requests
* The upstream service returns an error

### Fallback Dataset

The fallback generator creates an illustrative dataset containing approximately 260 earthquake events distributed across multiple real seismically active regions.

The synthetic dataset includes:

* Geographical clustering
* Real-world regional names
* Valid latitude/longitude coordinates
* Realistic magnitude distribution
* USGS-style place descriptions
* Recent timestamps

The fallback dataset is intended for **application continuity and demonstration**, not scientific research.

---

## 🧮 Analytical Methods

### Magnitude Filtering

Earthquakes are filtered using a configurable magnitude range:

```text
Minimum Magnitude ≤ Event Magnitude ≤ Maximum Magnitude
```

### Daily Frequency

Events are grouped by calendar date to calculate:

```text
Events per Day
Average Magnitude per Day
```

### Significant Events

Events satisfying:

```text
Magnitude ≥ 6.0
```

are classified as significant events for dashboard alerting.

### Risk-Zone Aggregation

Geographical coordinates are assigned to grid cells.

Each cell is then evaluated using:

```text
Event Count
Maximum Magnitude
```

The zones are ranked by event activity.

This approach is intentionally simple and explainable.

---

## 🧪 Testing

The project includes a comprehensive automated test suite.

### Test Suite

**66 tests passing**

Run the complete suite with:

```bash
python -m pytest tests/ -v
```

### Testing Coverage

The test suite validates:

* Fallback dataset generation
* Magnitude distribution
* Coordinate validity
* Deterministic snapshot generation
* USGS client behavior
* Network failure handling
* Successful live responses
* Source identification
* Magnitude filtering
* Place-name searching
* Daily frequency analysis
* Significant-event detection
* Risk-zone aggregation
* Map layer generation
* Marker generation
* End-to-end report construction

### Deterministic Data Generation

The fallback generator supports an explicit reference time:

```python
generate_snapshot(seed=42, now=fixed_time)
```

This allows tests to reproduce exactly the same dataset across multiple executions.

---

## 🐛 Engineering Lesson: Timestamp Determinism

During development, the fallback dataset generator exposed a subtle reproducibility problem.

The random components were deterministic when a fixed seed was supplied, but timestamps were generated using the current system time internally.

As a result:

```text
Run 1 → 12:00:00.123
Run 2 → 12:00:00.456
```

Although the random content was identical, timestamps differed.

### Solution

The function was redesigned to accept an explicit clock:

```python
generate_snapshot(
    seed=42,
    now=fixed_time,
)
```

Normal application usage can still default to the current time, while tests can provide a fixed timestamp.

This improves:

* Reproducibility
* Test reliability
* Debugging
* Deterministic behavior

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/earthquake-data-visualizer.git
cd earthquake-data-visualizer
```

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

### Generate a Text Analysis Report

```bash
python main.py --report --min-magnitude 4.5
```

### Search by Location

```bash
python main.py --report --place Alaska
```

### Generate an Interactive HTML Map

```bash
python main.py --map --output data/earthquake_map.html
```

### Launch the Streamlit Dashboard

```bash
streamlit run app.py
```

The application will open in your browser.

---

## ☁️ Deployment

### Streamlit Community Cloud

Streamlit Community Cloud is the recommended deployment option for this project.

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud.
3. Connect your GitHub account.
4. Select the repository.
5. Select the `main` branch.
6. Set the application entry point to:

```text
app.py
```

7. Deploy.

The application is designed to attempt the live USGS feed automatically when deployed in an environment with outbound network access.

### Render

The application can also be deployed as a Streamlit service.

**Build command:**

```bash
pip install -r requirements.txt
```

**Start command:**

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

### Hugging Face Spaces

The project can also be adapted for a Streamlit-based Hugging Face Space.

---

## 🎨 Design Decisions

### Map-First Interface

A map is the most natural interface for geographical earthquake data.

Therefore, the dashboard prioritizes:

```text
Map
 ↓
KPIs
 ↓
Analytics
 ↓
Detailed Data
```

rather than hiding the map inside a secondary tab.

### Single Orchestration Layer

`visualizer_service.py` provides a centralized application pipeline.

This prevents `app.py` and `main.py` from duplicating business logic.

### Honest Data Status

The application treats the data source as part of the dataset itself.

Instead of relying only on logs, the UI explicitly communicates whether the current dataset is:

```text
LIVE USGS DATA
```

or:

```text
CACHED FALLBACK DATA
```

This is particularly important when synthetic data is involved.

### Explainable Risk Zones

The project intentionally avoids presenting a simple event-count aggregation as a scientific seismic hazard model.

The risk-zone system answers:

> **"Where has earthquake activity been concentrated in the selected dataset?"**

It does **not** claim to answer:

> **"Where will the next damaging earthquake occur?"**

---

## ⚠️ Limitations

This project is designed for **data visualization, exploration, and portfolio demonstration**.

It should not be used for:

* Emergency response
* Official seismic hazard assessment
* Earthquake prediction
* Scientific hazard modeling
* Disaster-management decisions

The grid-based risk zones are analytical visualizations rather than validated seismic hazard maps.

Similarly, the fallback dataset is illustrative synthetic data and should not be interpreted as actual earthquake observations.

---

## 🗺️ Future Roadmap

### Version 2.0

Planned improvements include:

* [ ] Real seismic hazard overlays
* [ ] USGS ShakeMap integration
* [ ] Historical earthquake comparison
* [ ] Time-lapse earthquake animation
* [ ] Aftershock analysis
* [ ] Tsunami-related event indicators
* [ ] Population-weighted impact estimation
* [ ] Region watchlists
* [ ] Configurable earthquake alerts
* [ ] Push notifications
* [ ] Multi-source earthquake comparison
* [ ] EMSC data integration
* [ ] Advanced geospatial clustering
* [ ] Interactive historical timeline

---

## 🤝 Contributing

Contributions are welcome.

### Development Workflow

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/your-feature
```

3. Follow the existing coding standards.
4. Add tests for new functionality.
5. Run the test suite:

```bash
python -m pytest tests/ -v
```

6. Commit your changes.
7. Push the branch.
8. Open a Pull Request.

### Code Quality Guidelines

New code should follow:

* PEP 8
* Type hints
* Google-style docstrings
* Clear naming
* Modular design
* Appropriate logging
* Input validation
* Automated tests

---

## 📄 License

This project is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for details.

---

## 👨‍💻 Author

**Sumair Ahmed Dero**

BS Artificial Intelligence Student | AI/ML Developer | Python Developer

Interested in:

* Artificial Intelligence
* Machine Learning
* Data Science
* Computer Vision
* Natural Language Processing
* Robotics
* AI Research
* Production AI Systems

This project was developed as part of a continuous portfolio-building journey focused on creating practical, production-oriented software projects.

---

## ⭐ Support

If you find this project useful or interesting, consider giving the repository a ⭐ on GitHub.

Your feedback and contributions are welcome.
