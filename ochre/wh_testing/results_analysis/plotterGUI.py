# Plotter

import sys
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class CSVPlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Data Plotter")
        self.setGeometry(100, 100, 800, 600)
        
        self.layout = QVBoxLayout()
        
        self.load_button = QPushButton("Load CSV")
        self.load_button.clicked.connect(self.load_csv)
        self.layout.addWidget(self.load_button)
        
        self.metric_label = QLabel("Select Metric:")
        self.layout.addWidget(self.metric_label)
        
        self.metric_selector = QComboBox()
        self.metric_selector.currentIndexChanged.connect(self.plot_data)
        self.layout.addWidget(self.metric_selector)
        
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        self.setLayout(self.layout)
        self.df = None
    
    def load_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            self.df = pd.read_csv(file_name, parse_dates=[0])  # Assuming first column is timestamps
            if len(self.df.columns) > 1:
                self.metric_selector.clear()
                self.metric_selector.addItems(self.df.columns[1:])

    
    def plot_data(self):
        if self.df is not None and self.metric_selector.count() > 0:
            self.ax.clear()
            metric = self.metric_selector.currentText()
            self.ax.plot(self.df.iloc[:, 0], self.df[metric], label=metric)
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel(metric)
            self.ax.legend()
            self.ax.grid()
            self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVPlotter()
    window.show()
    sys.exit(app.exec())
