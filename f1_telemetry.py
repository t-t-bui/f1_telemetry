import sys
import os
import fastf1
import pandas as pd
import numpy as np


from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton, 
	QLineEdit, QComboBox, QCheckBox, QRadioButton, QTextEdit, QSlider, QSpinBox, 
	QProgressBar, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
	QWidget, QMessageBox, QStackedWidget, QFrame, QGridLayout)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import matplotlib.pyplot as plt
import warnings

# Enable caching for fastf1
if not os.path.exists("fastf1_cache"):
	os.makedirs("fastf1_cache")

fastf1.Cache.enable_cache("fastf1_cache")

# Baseic Telemetry screen
class BasicTelemetryWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.layout = QVBoxLayout(self)
		self.setup_inputs()
		self.setup_matplotlib()

	def setup_inputs(self):
		input_layout = QHBoxLayout()
		self.year_input = QLineEdit("2023")
		self.event_input = QLineEdit("Monza")
		self.session_input = QLineEdit("Q")
		self.driver_input = QLineEdit("VER")

		for label, widget in [("Year:", self.year_input), ("Event:", self.event_input), ("Session:", self.session_input), ("Driver:", self.driver_input)]:
			input_layout.addWidget(QLabel(label))
			input_layout.addWidget(widget)

		self.load_btn = QPushButton("Load Telemetry...")
		self.load_btn.clicked.connect(self.load_data)
		input_layout.addWidget(self.load_btn)

		self.layout.addLayout(input_layout)

		self.lap_time_label = QLabel("Fastest Lap Time: N/A")
		self.lap_time_label.setAlignment(Qt.AlignCenter)
		self.layout.addWidget(self.lap_time_label)

	def setup_matplotlib(self):
		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.ax = self.figure.add_subplot(111)
		self.ax.set_axis_off()
		self.layout.addWidget(self.canvas)

	def load_data(self):
		year_str, event, session_identifier, driver = (
			self.year_input.text().strip(), self.event_input.text().strip(), self.session_input.text().strip().upper(), self.driver_input.text().strip().upper()
			)
		if not all([year_str, event, session_identifier, driver]): 
			return

		self.lap_time_label.setText("Loading data...")
		QApplication.processEvents()

		try:
			session = fastf1.get_session(int(year_str), event, session_identifier)
			session.load(telemetry=True, laps=True, weather=False)
			fastest_lap = session.laps.pick_drivers(driver).pick_fastest()
			lap_time = fastest_lap['LapTime']
			lap_time_str = f"{int(lap_time.total_seconds() // 60):02d}:{lap_time.total_seconds() % 60:06.3f}"

			self.lap_time_label.setText(f"{driver} Fastest Lap Time: {lap_time_str}")
			telemetry = fastest_lap.get_telemetry()

			self.ax.clear()
			self.ax.plot(telemetry['X'], telemetry['Y'], color='blue', linewidth=3)
			self.ax.set_aspect('equal')
			self.ax.set_axis_off()
			self.canvas.draw()
		except Exception as e:
			self.lap_time_label.setText("Error loading data.")

class AdvanceTelemetryWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.setStyleSheet("background-color: #111111; color: white; font-family: sans-serif;")
		self.layout = QVBoxLayout(self)

		header = QLabel("F1")
		header.setStyleSheet("font-size: 24px; font-weight: bold; font-style: italic; padding: 10px;")
		self.layout.addWidget(header)

		middle_layout = QHBoxLayout()

		driver1_panel = self.create_driver_panel("1", "CHARLES\nLECLERC", "FERRARI", "1:23.456", "-0.321s", "#FF2800", [81, 5, 14])
		middle_layout.addWidget(driver1_panel)

		self.map_canvas = self.create_dark_canvas()
		middle_layout.addWidget(self.map_canvas, 2)

		driver2_panel = self.create_driver_panel("2", "CARLOS\nSAINZ", "FERRARI", "1:23.777", "+0.321s", "#FFF200", [81, 5, 14])
		middle_layout.addWidget(driver2_panel)

		self.layout.addLayout(middle_layout, 2)

		self.graph_canvas = self.create_dark_canvas(subplots = 2)
		self.layout.addWidget(self.graph_canvas, 3)

		self.draw_mockup_data()

	def create_driver_panel(self, pos, name, team, lap_time, gap, color, stats):
		panel = QFrame()
		layout = QVBoxLayout(panel)

		header_layout = QVBoxLayout()
		pos_label = QLabel(pos)
		pos_label.setStyleSheet("font-size: 36px; font-weight: bold;")
		name_label = QLabel(name)
		name_label.setStyleSheet(f"font-size: 18px; font-weight: bold; font-style: italic; color: {color};")
		team_label = QLabel(team)
		team_label.setStyleSheet("font-size: 10px; color: gray;")

		name_vbox = QVBoxLayout()
		name_vbox.addWidget(name_label)
		name_vbox.addWidget(team_label)

		header_layout.addWidget(pos_label)
		header_layout.addLayout(name_vbox)
		header_layout.addStretch()
		layout.addLayout(header_layout)

		times_layout = QHBoxLayout()
		times_layout.addWidget(self.styled_label("LAP TIME", lap_time, "24px"))
		times_layout.addWidget(self.styled_label("GAP", gap, "24px"))
		layout.addLayout(times_layout)

		labels = ["FULL THROTTLE", "HEAVY BREAKING", "CORNERING"]
		for label in labels:
			stat_layout = QHBoxLayout()
			stat_label = QLabel(label)
			stat_label.setStyleSheet("font-size: 10px; color: gray;")
			val_label = QLabel(f"{label}%")
			val_label.setStyleSheet("font-size: 12px; font-weight: bold;")

			bar_bg = QFrame()
			bar_bg.setFixedHeight(4)
			bar_bg.setStyleSheet("background-color: #333333;")

			stat_layout.addWidget(stat_label)
			stat_layout.addWidget(bar_bg, 1)
			stat_layout.addWidget(val_label)
			layout.addLayout(stat_layout)

		layout.addStretch()
		return panel

	def styled_label(self, title, value, val_size):
		vbox = QVBoxLayout()
		t = QLabel(title)
		t.setStyleSheet("font-size: 10px; color: gray;")
		v = QLabel(value)
		v.setStyleSheet(f"font-size: {val_size}; font-weight: bold; font-style: italic;")
		vbox.addWidget(t)
		vbox.addWidget(v)

		container = QWidget()
		container.setLayout(vbox)
		return container

	def create_dark_canvas(self, subplots = 1):
		fig = Figure(facecolor = '#111111')
		canvas = FigureCanvas(fig)

		if subplots == 1:
			ax = fig.add_subplot(111)
			ax.set_facecolor('#111111')
			ax.set_axis_off()
			canvas.ax = ax
		else: 
			gs = fig.add_gridspec(4,1)
			ax1 = fig.add_subplot(gs[0:3, 0])
			ax2 = fig.add_subplot(gs[3, 0])
			for ax in [ax1, ax2]:
				ax.set_facecolor('#111111')
				ax.tick_params(colors = 'white')
				for spine in ax.spines.values():
					spine.set_color('#333333')
			canvas.ax1 = ax1
			canvas.ax2 = ax2

		return canvas

	def draw_mockup_data(self):
		self.map_canvas.ax.plot([0,1,1.5,0.5,0], [1,0,0,1.5,1], color='#FF2800', linewidth=3)
		self.map_canvas.ax.plot([0.1,1.1,1.6,0.6,0.1], [0.9,-0.1,-0.1,1.4,0.9], color='#FFF200', linewidth=2)
		self.map_canvas.draw()

		x = np.linspace(0,10,100)
		y1 = np.abs(np.sin(x)) * 300 + 50
		y2 = np.abs(np.sin(x + 0.1)) * 299 + 50

		self.graph_canvas.ax1.plot(x, y1, color='#FF2800', label='LEC')
		self.graph_canvas.ax1.plot(x, y2, color='#FFF200', label='SAI')
		self.graph_canvas.ax1.set_ylabel("SPEED km/h", color="gray")

		self.graph_canvas.ax2.plot(x, y1-y2, color='#FF2800')
		self.graph_canvas.ax2.set_ylabel("DELTA", color="gray")
		self.graph_canvas.draw()


class F1TelemetryApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("FastF1 Telemetry Viewer")
		self.resize(1200,800)

		self.main_widget = QWidget()
		self.setCentralWidget(self.main_widget)
		self.layout = QVBoxLayout(self.main_widget)

		nav_layout = QHBoxLayout()
		self.btn_basic = QPushButton("Basic Telemetry")
		self.btn_adv = QPushButton("Advance Telemetry")

		self.btn_basic.clicked.connect(lambda: self.stack.setCurrentIndex(0))
		self.btn_adv.clicked.connect(lambda: self.stack.setCurrentIndex(1))

		nav_layout.addWidget(self.btn_basic)
		nav_layout.addWidget(self.btn_adv)
		self.layout.addLayout(nav_layout)

		self.stack = QStackedWidget()
		self.basic_view = BasicTelemetryWidget()
		self.advanced_view = AdvanceTelemetryWidget()

		self.stack.addWidget(self.basic_view)
		self.stack.addWidget(self.advanced_view)

		self.layout.addWidget(self.stack)

if __name__ == "__main__":
	app = QApplication(sys.argv)

	# Global styles for buttons and inputs
	app.setStyleSheet("""
		QPushButton { background-color: #333; color: white; padding: 8px; border-radius: 4px; }
		QPushButton:hover { background-color: #555 }
		QLineEdit { background-color: #222; color: white; padding: 5px; border: 1px solid #444; }
		""")
	window = F1TelemetryApp()
	window.show()
	sys.exit(app.exec())
