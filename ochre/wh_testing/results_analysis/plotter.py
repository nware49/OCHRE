import sys
import os
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
        
        self.load_button = QPushButton("Load CSVs")
        self.load_button.clicked.connect(self.load_csvs)
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
        self.dataframes = []
        self.file_names = []
    
    def load_csvs(self):
        current_directory = os.path.join(os.getcwd(), "ochre\\wh_tests\\results")
        files, _ = QFileDialog.getOpenFileNames(self, "Open CSV Files", current_directory, "CSV Files (*.csv);;All Files (*)")
        if files:
            self.dataframes = []
            self.file_names = files
            for file in files:
                df = pd.read_csv(file, parse_dates=[0])  # Assuming first column is timestamps
                self.dataframes.append(df)
            
            if self.dataframes:
                common_metrics = set(self.dataframes[0].columns[1:])
                for df in self.dataframes[1:]:
                    common_metrics.intersection_update(df.columns[1:])
                
                self.metric_selector.clear()
                self.metric_selector.addItems(sorted(common_metrics))
                
    def plot_data(self):
        if self.dataframes and self.metric_selector.count() > 0:
            self.ax.clear()
            metric = self.metric_selector.currentText()
            
            for df, file in zip(self.dataframes, self.file_names):
                self.ax.plot(df.iloc[:, 0], df[metric], label=file.split('/')[-1])
                
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
