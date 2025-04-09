import json
import pyqtgraph as pg
from simworld.config import Config
import random

from simworld.citygen.dataclass import (
    Bounds, Building, BuildingType, Detail, DetailType
)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from typing import List

class CityData:
    """Container for city visualization data"""
    def __init__(self):
        self.roads: List[dict] = []  # Using dict for roads since no Road class in custom_types
        self.buildings: List[Building] = []
        self.details: List[Detail] = []

    def load_from_files(self, output_dir = "output"):
        """Load city data from JSON files"""
        roads_path = f"{output_dir}/roads.json"
        buildings_path = f"{output_dir}/buildings.json"
        details_path = f"{output_dir}/details.json"
        try:
            # Load roads
            with open(roads_path, 'r') as f:
                roads_data = json.load(f)
                self.roads = roads_data['roads']  # Store as raw dict

            # Load buildings
            with open(buildings_path, 'r') as f:
                buildings_data = json.load(f)
                self.buildings = []
                for b in buildings_data['buildings']:
                    building_type = BuildingType(
                        name=b['type'],
                        width=b['bounds']['width'],
                        height=b['bounds']['height']
                    )
                    bounds = Bounds(
                        x=b['bounds']['x'],
                        y=b['bounds']['y'],
                        width=b['bounds']['width'],
                        height=b['bounds']['height'],
                        rotation=b['bounds']['rotation']
                    )
                    self.buildings.append(Building(
                        building_type=building_type,
                        bounds=bounds,
                        rotation=b['rotation']
                    ))

            # Load details
            with open(details_path, 'r') as f:
                details_data = json.load(f)
                self.details = []
                for d in details_data['details']:
                    detail_type = DetailType(
                        name=d['type'],
                        width=d['bounds']['width'],
                        height=d['bounds']['height']
                    )
                    bounds = Bounds(
                        x=d['bounds']['x'],
                        y=d['bounds']['y'],
                        width=d['bounds']['width'],
                        height=d['bounds']['height'],
                        rotation=d['bounds']['rotation']
                    )
                    self.details.append(Detail(
                        detail_type=detail_type,
                        bounds=bounds,
                        rotation=d['rotation']
                    ))

            print("Successfully loaded city data")

        except Exception as e:
            print(f"Error loading city data: {e}")

class CityVisualizer(QMainWindow):
    """Visualization renderer for city data"""
    def __init__(self, config: Config):
        """Initialize visualizer"""
        super().__init__()
        self.setWindowTitle("City Visualization")

        # Create main window widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        main_layout = QVBoxLayout(self.main_widget)

        # Create title label
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "QLabel {color: #34495E;font-size: 14px;font-weight: bold;padding: 5px;}"
        )
        main_layout.addWidget(self.title_label)

        # Create plot window
        self.plot_widget = pg.PlotWidget()
        main_layout.addWidget(self.plot_widget)

        # Set plot style
        self.plot_widget.setBackground("#F0F8FF")
        self.plot_widget.showGrid(True, True, alpha=0.3)
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setXRange(config['citygen.quadtree_bounds.x'], config['citygen.quadtree_bounds.x'] + config['citygen.quadtree_bounds.width'])
        self.plot_widget.setYRange(config['citygen.quadtree_bounds.y'], config['citygen.quadtree_bounds.y'] + config['citygen.quadtree_bounds.height'])
        
        # 添加这一行来翻转 y 轴
        self.plot_widget.getViewBox().invertY(True)

        # Enable mouse interaction
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.setMenuEnabled(False)

        # Initialize city data
        self.city = CityData()
        self.city.load_from_files(output_dir=config['citygen.output_dir'])

        # Set window size
        self.resize(1280, 960)

    def draw_frame(self):
        """Draw current state of the city"""
        self.plot_widget.clear()

        # Draw roads
        highways = []
        normal_roads = []
        for road in self.city.roads:
            points = [
                (road['start']['x'], road['start']['y']),
                (road['end']['x'], road['end']['y']),
            ]
            if road['is_highway']:
                highways.extend(points)
            else:
                normal_roads.extend(points)

        # Draw normal roads
        if normal_roads:
            for i in range(0, len(normal_roads), 2):
                line = pg.PlotDataItem(
                    x=[normal_roads[i][0], normal_roads[i + 1][0]],
                    y=[normal_roads[i][1], normal_roads[i + 1][1]],
                    pen=pg.mkPen("#2E5984", width=1.8),
                    antialias=True,
                )
                self.plot_widget.addItem(line)

        # Draw highways
        if highways:
            for i in range(0, len(highways), 2):
                line = pg.PlotDataItem(
                    x=[highways[i][0], highways[i + 1][0]],
                    y=[highways[i][1], highways[i + 1][1]],
                    pen=pg.mkPen("#1E3F66", width=3.0),
                    antialias=True,
                )
                self.plot_widget.addItem(line)

        # Generate random colors for each building type
        building_colors = {}
        for building in self.city.buildings:
            building_type = building.building_type.name
            if building_type not in building_colors:
                # Generate random RGB values with good visibility
                r = random.randint(100, 255)
                g = random.randint(100, 255)
                b = random.randint(100, 255)
                building_colors[building_type] = f"#{r:02x}{g:02x}{b:02x}"

        # Draw buildings
        for building in self.city.buildings:
            rect = pg.QtWidgets.QGraphicsRectItem(
                building.bounds.x,
                building.bounds.y,
                building.bounds.width,
                building.bounds.height,
            )

            rect.setTransformOriginPoint(
                building.bounds.x + building.bounds.width / 2,
                building.bounds.y + building.bounds.height / 2,
            )
            rect.setRotation(building.rotation)

            building_type = building.building_type.name
            color = building_colors[building_type]
            rect.setPen(pg.mkPen(color, width=2))
            rect.setBrush(pg.mkBrush(color))
            self.plot_widget.addItem(rect)

        # Generate random colors for each detail type
        detail_colors = {}
        for detail in self.city.details:
            detail_type = detail.detail_type.name
            if detail_type not in detail_colors:
                # Generate random RGB values with good visibility
                r = random.randint(100, 255)
                g = random.randint(100, 255)
                b = random.randint(100, 255)
                detail_colors[detail_type] = f"#{r:02x}{g:02x}{b:02x}"

        # Draw details
        for detail in self.city.details:
            size = min(detail.bounds.width, detail.bounds.height) * 1
            detail_type = detail.detail_type.name
            color = detail_colors[detail_type]
            
            circle = pg.ScatterPlotItem(
                pos=[(detail.center.x, detail.center.y)],
                size=size,
                pen=pg.mkPen('w'),  # White border
                brush=pg.mkBrush(color),
                symbol='o',
                antialias=True,
                pxMode=False
            )
            self.plot_widget.addItem(circle)

        # Update status bar information
        stats_text = f"ROADS: {len(self.city.roads)} | BUILDINGS: {len(self.city.buildings)} | DETAILS: {len(self.city.details)}"
        self.title_label.setText(stats_text)

def main(config: Config):
    """Main function"""
    app = QApplication([])
    app.setStyle("Fusion")

    visualizer = CityVisualizer(config=config)
    visualizer.show()
    visualizer.draw_frame()

    app.exec_()

if __name__ == "__main__":
    main(config=Config()) 