import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class CSVPlotter(QWidget):
    def __init__(self, directory, file_list):
        super().__init__()
        self.setWindowTitle("Hot Water Trace Response Plotter")
        self.resize(800, 600)  # Allow window to be resized dynamically

        self.layout = QVBoxLayout()

        self.metric_label = QLabel("Select Metric:")
        self.layout.addWidget(self.metric_label)

        self.metric_selector = QComboBox()
        self.metric_selector.currentIndexChanged.connect(self.plot_data)
        self.layout.addWidget(self.metric_selector)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, stretch=1)  # Allows dynamic resizing

        self.setLayout(self.layout)
        self.dataframes = []
        self.file_names = []
        
        self.load_csvs(directory, file_list)
    
    def load_csvs(self, directory, file_list):
        files = [os.path.join(directory, file) for file in file_list]
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
                self.ax.plot(df.iloc[:, 0], df[metric], label=os.path.basename(file))
                
            self.ax.set_title(str("Hot Water Trace Response " + metric))    
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel(metric)
            self.ax.legend()
            self.ax.grid()
            self.canvas.draw()

if __name__ == "__main__":
    directory = "C:/Users/natha/OneDrive/Documents/College Work/Thesis/OCHRE-ese-wh/OCHRE/ochre/wh_tests/results/continuous_12S1279_trace/"  # Change this to the desired directory
    file_list = ["Electric Resistance Water Heater.csv", "ESE Heat Pump Water Heater.csv", "Gas Tankless Water Heater.csv", "Gas Water Heater.csv", "Heat Pump Water Heater.csv", "Low Power Heat Pump Water Heater.csv", "Tankless Water Heater.csv"]  # Provide the list of CSV filenames
    #file_list = ["Water Tank_Electric Resistance Water Heater.csv", "Water Tank_ESE Heat Pump Water Heater.csv", "Water Tank_Gas Tankless Water Heater.csv", "Water Tank_Gas Water Heater.csv", "Water Tank_Heat Pump Water Heater.csv", "Water Tank_Low Power Heat Pump Water Heater.csv", "Water Tank_Tankless Water Heater.csv"] 
    #water_tank_file_list = [f"Water Tank_{file}" for file in file_list]

    app = QApplication(sys.argv)
    window = CSVPlotter(directory, file_list)
    window.show()
    sys.exit(app.exec())
