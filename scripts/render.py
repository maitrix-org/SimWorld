"""City renderer module for visualizing road networks, buildings and other urban elements."""
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton,
                             QVBoxLayout, QWidget)

from simworld.citygen.city.city_generator import CityGenerator
from simworld.config import Config
from simworld.utils.data_exporter import DataExporter


class CityRenderer(QMainWindow):
    """Visualization renderer for city road network.

    This class provides a GUI interface for visualizing and interacting with
    the city generation process.
    """

    def __init__(self, config: Config):
        """Initialize renderer.

        Args:
            config: Configuration object containing city generation parameters.
        """
        super().__init__()

        self.config = config

        self.setWindowTitle('City Road Network Generator')

        # Create main window widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        main_layout = QVBoxLayout(self.main_widget)

        # Create title label
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            'QLabel {color: #34495E;font-size: 14px;font-weight: bold;padding: 5px;}'
        )
        main_layout.addWidget(self.title_label)

        # Create plot window
        self.plot_widget = pg.PlotWidget()
        main_layout.addWidget(self.plot_widget)

        # Add a save button
        self.output = config['citygen.output_dir']
        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save)
        main_layout.addWidget(self.save_button)

        # Set plot style
        self.plot_widget.setBackground('#F0F8FF')
        self.plot_widget.showGrid(True, True, alpha=0.3)
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setXRange(self.config['citygen.quadtree.bounds.x'], self.config['citygen.quadtree.bounds.x'] + self.config['citygen.quadtree.bounds.width'])
        self.plot_widget.setYRange(self.config['citygen.quadtree.bounds.y'], self.config['citygen.quadtree.bounds.y'] + self.config['citygen.quadtree.bounds.height'])

        # Enable mouse interaction
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.setMenuEnabled(False)

        # Initialize city generator
        self.city = CityGenerator(self.config)

        # Set timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_generation)
        self.timer.setInterval(1)  # Set longer interval, e.g. 10ms

        # Set window size
        self.resize(1280, 720)

    def draw_frame(self):
        """Draw current state of the city.

        This method renders the current state of roads, buildings,
        intersections, and other city elements.
        """
        self.plot_widget.clear()

        # Get all segments
        visible_segments = self.city.roads

        # Divide roads into highways and normal roads
        highways = []
        normal_roads = []
        for segment in visible_segments:
            points = [
                (segment.start.x, segment.start.y),
                (segment.end.x, segment.end.y),
            ]
            if segment.q.highway:
                highways.extend(points)
            else:
                normal_roads.extend(points)

        # Draw normal roads
        if normal_roads:
            for i in range(0, len(normal_roads), 2):
                line = pg.PlotDataItem(
                    x=[normal_roads[i][0], normal_roads[i + 1][0]],
                    y=[normal_roads[i][1], normal_roads[i + 1][1]],
                    pen=pg.mkPen('#2E5984', width=1.8),
                    antialias=True,
                )
                self.plot_widget.addItem(line)

        # Draw highways
        if highways:
            for i in range(0, len(highways), 2):
                line = pg.PlotDataItem(
                    x=[highways[i][0], highways[i + 1][0]],
                    y=[highways[i][1], highways[i + 1][1]],
                    pen=pg.mkPen('#1E3F66', width=3.0),
                    antialias=True,
                )
                self.plot_widget.addItem(line)

        # Draw intersections
        if self.city.intersections:
            intersection_points = [(i.point.x, i.point.y) for i in self.city.intersections]
            if intersection_points:
                scatter = pg.ScatterPlotItem(
                    pos=intersection_points,
                    size=8,
                    brush=pg.mkBrush('#D4AF37'),
                    pen=None,
                    antialias=True,
                )
                self.plot_widget.addItem(scatter)

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

            if building.building_type.name in self.city.building_colors:
                rect.setPen(pg.mkPen(self.city.building_colors[building.building_type.name], width=2))
                rect.setBrush(pg.mkBrush(self.city.building_colors[building.building_type.name]))
            else:
                rect.setPen(pg.mkPen('#2C3E50', width=1))
                rect.setBrush(pg.mkBrush('#34495E'))
            self.plot_widget.addItem(rect)

        # Draw details
        for element in self.city.elements:
            # Calculate circle size based on bounding box
            size = min(element.bounds.width, element.bounds.height) * 1.4  # Diameter is 1.4 times the length
            # Create circle at detail's center
            circle = pg.ScatterPlotItem(
                pos=[(element.bounds.x + element.bounds.width/2,
                      element.bounds.y + element.bounds.height/2)],
                size=size,
                pen=pg.mkPen('w'),  # White border
                brush=pg.mkBrush(self.city.element_colors[element.element_type.name]),
                symbol='o',
                antialias=True,
                pxMode=False  # Disable pixel mode to use actual size units
            )
            self.plot_widget.addItem(circle)

        # Update status bar information
        stats_text = f'ROADS: {len(visible_segments)} | BUILDINGS: {len(self.city.buildings)} | ELEMENTS: {len(self.city.elements)}'
        self.title_label.setText(stats_text)

        # Draw routes
        for route in self.city.routes:
            points = [(point.x, point.y) for point in route.points]
            line = pg.PlotDataItem(
                x=[p[0] for p in points],
                y=[p[1] for p in points],
                pen=pg.mkPen('#D4AF37', width=2),
                antialias=True
            )
            self.plot_widget.addItem(line)

    def update_generation(self):
        """Update city generation process.

        This method is called by the timer to step through the city generation
        process and update the display.
        """
        if not self.city.is_generation_complete():
            self.city.generate_step()
            self.draw_frame()
            # print(f"Roads: {len(self.city.roads)}, Buildings: {len(self.city.buildings)}, Details: {len(self.city.details)}")  # Debug info
        else:
            print('Generation completed!')
            self.timer.stop()

    def start_generation(self):
        """Start generation process.

        Initiates the city generation process and starts the visualization timer.
        """
        print('Starting generation...')
        self.timer.start()
        self.draw_frame()

    def save(self):
        """Save the current plot as an image.

        Saves the current visualization as a PNG image and exports city data
        to JSON format.
        """
        pixmap = QPixmap(self.plot_widget.size())
        painter = QPainter(pixmap)
        self.plot_widget.render(painter)
        painter.end()

        if pixmap.save(f'{self.output}/city_map.png', 'PNG'):
            print('Image saved successfully as city_map.png')
        else:
            print('Failed to save image')

        exporter = DataExporter(self.city)
        exporter.export_to_json(self.output)
        print(f'City generation completed. Data exported to {self.output} directory.')


def main():
    """Main function to run the city renderer application."""
    app = QApplication([])
    app.setStyle('Fusion')

    renderer = CityRenderer(config=Config())
    renderer.show()
    renderer.start_generation()

    app.exec_()


if __name__ == '__main__':
    main()
