import sys
import os
import fastf1
import pandas as pd

from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton, 
	QLineEdit, QComboBox, QCheckBox, QRadioButton, QTextEdit, QSlider, QSpinBox, 
	QProgressBar, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
	QWidget, QMessageBox)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


if not os.path.exists("fastf1_cache"):
	os.makedirs("fastf1_cache")
fastf1.Cache.enable_cache("fastf1_cache")

class F1TelemetryApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("FastF1 Viewer")
		self.resize(800,700)

		self.main_widget = QWidget()
		self.setCentralWidget(self.main_widget)
		self.layout = QVBoxLayout(self.main_widget)

		# setup UI componenets
		self.setup_inputs()
		self.setup_matplotlib()

	def setup_inputs(self):
		input_layout = QHBoxLayout()

		# year input
		self.year_input = QLineEdit("2023")
		self.year_input.setPlaceholderText("Year (e.g. 2023)")
		input_layout.addWidget(QLabel("Year:"))
		input_layout.addWidget(self.year_input)

		# Event Input
		self.event_input = QLineEdit("Monaco")
		self.event_input.setPlaceholderText("Event (e.g. Monaco)")
		input_layout.addWidget(QLabel("Event:"))
		input_layout.addWidget(self.event_input)

		# Session Input
		self.session_input = QLineEdit("Q")
		self.session_input.setPlaceholderText("Session (e.g. Q, R, FP1)")
		input_layout.addWidget(QLabel("Session:"))
		input_layout.addWidget(self.session_input)

		# Driver Input
		self.driver_input = QLineEdit("Ver")
		self.driver_input.setPlaceholderText("Drive (e.g. Ver)")
		input_layout.addWidget(QLabel("Driver:"))
		input_layout.addWidget(self.driver_input)

		# Load Button
		self.load_btn = QPushButton("Load Telemetry")
		self.load_btn.clicked.connect(self.load_data)
		input_layout.addWidget(self.load_btn)

		self.layout.addLayout(input_layout)

		# Lap Time Display Label
		self.lap_time_label = QLabel("Fastest Lap Time: N/A")
		self.lap_time_label.setAlignment(Qt.AlignCenter)
		self.lap_time_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px")
		self.layout.addWidget(self.lap_time_label)

	def setup_matplotlib(self):
		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.ax = self.figure.add_subplot(111)
		self.ax.set_axis_off()
		self.layout.addWidget(self.canvas)

	def load_data(self):
		year_str = self.year_input.text().strip()
		event = self.event_input.text().strip()
		session_identifier = self.session_input.text().strip().upper()
		driver = self.driver_input.text().strip().upper()

		if not (year_str and event and session_identifier and driver):
			QMessageBox.warning(self, "Input Error", "Please fill out all fields.")
			return

		try:
			year = int(year_str)
		except Valueerror:
			QMessageBox.warning(self, "Input Error", "Year must be a number.")
			return

		self.lap_time_label.setText("Loading data... This may take a moment.")
		QApplication.processEvents()

		try:
			session = fastf1.get_session(year, event, session_identifier) 
			session.load(telemetry=True, laps=True, weather=False)

			laps = session.laps.pick_drivers(driver)
			if laps.empty:
				raise Valueerror(f"No laps found for driver {driver}.")

			fastest_lap = laps.pick_fastest()

			lap_time = fastest_lap['LapTime']
			if pd.isnull(lap_time):
				lap_time_str = "No valid lap time recorded."
			else:
				total_seconds = lap_time.total_seconds()
				minutes = int(total_seconds // 60)
				seconds = total_seconds % 60
				lap_time_str = f"{minutes:02d}:{seconds:06.3f}"

			self.lap_time_label.setText(f"{driver} Fastest Lap Time: {lap_time_str}")

			telemetry = fastest_lap.get_telemetry()
			x = telemetry['X']
			y = telemetry['Y']

			self.ax.clear()
			self.ax.plot(x, y, color='blue', linewidth=3)
			self.ax.set_title(f"{year} {event} Track Map ({session_identifier})", fontsize=14)
			self.ax.set_aspect('equal')
			self.ax.set_axis_off()
			self.canvas.draw()

		except Exception as e:
			self.lap_time_label.setText("Error loading data.")
			QMessageBox.critical(self, "Error", f"Failed to load telemetry:\n{str(e)}")

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = F1TelemetryApp()
	window.show()
	sys.exit(app.exec())