import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class AverageDayPlotter(QWidget):
    def __init__(self, directory, file_list):
        super().__init__()
        self.setWindowTitle("Average Day Plotter")
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
            self.file_names = file_list  # Store file names for labeling
            for file in files:
                df = pd.read_csv(file, parse_dates=[0])  # Assuming first column is timestamps
                df['time'] = df.iloc[:, 0].dt.time  # Extract time
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
            
            avg_data = []
            for df, file_name in zip(self.dataframes, self.file_names):
                df['seconds_since_midnight'] = df['time'].apply(lambda t: t.hour * 3600 + t.minute * 60 + t.second)
                df_grouped = df.groupby(df['seconds_since_midnight'])[metric].mean()
                avg_data.append(df_grouped)
                self.ax.plot(df_grouped.index / 3600, df_grouped.values, label=f"{file_name} Avg")
            
            avg_day = pd.concat(avg_data, axis=1).mean(axis=1)
            self.ax.plot(avg_day.index / 3600, avg_day.values, label="Overall Avg", linestyle="dashed", linewidth=2)
            
            self.ax.set_title(str("Average Daily " + metric))  # Set title to match Y-axis label
            self.ax.set_xlabel("Time (Hours)")
            self.ax.set_ylabel(metric)
            self.ax.set_xticks(range(0, 25, 1))
            self.ax.set_xticklabels([f"{h}:00" for h in range(0, 25, 1)])  # Ensure correct number of labels
            self.ax.legend()
            self.ax.grid()
            self.canvas.draw()

if __name__ == "__main__":
    directory = "C:/Users/natha/OneDrive/Documents/College Work/Thesis/OCHRE-ese-wh/OCHRE/ochre/wh_tests/results/continuous_12S1279_trace/"  # Change this to the desired directory
    file_list = ["Electric Resistance Water Heater.csv", "ESE Heat Pump Water Heater.csv", "Gas Tankless Water Heater.csv", "Gas Water Heater.csv", "Heat Pump Water Heater.csv", "Low Power Heat Pump Water Heater.csv", "Tankless Water Heater.csv"]  # Provide the list of CSV filenames
    
    app = QApplication(sys.argv)
    window = AverageDayPlotter(directory, file_list)
    window.show()
    sys.exit(app.exec())
