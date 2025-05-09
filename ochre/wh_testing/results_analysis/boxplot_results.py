import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.size': 15,            # Base font size
    'axes.titlesize': 18,       # Title
    'axes.labelsize': 15,       # Axis labels
    'xtick.labelsize': 15,      # X tick labels
    'ytick.labelsize': 15,      # Y tick labels
    'legend.fontsize': 18,      # Legend text
})


def plot_boxplot(csv_file):
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    palette = ['plum', 'g', 'orange', 'b', 'r', 'magenta', 'grey', 'cyan']
    palette = ['mediumseagreen', 'firebrick', 'mediumseagreen', 'mediumseagreen', 'mediumseagreen', 'firebrick', 'mediumseagreen', 'mediumseagreen']

    # Melt the dataframe to have 'Architecture' and 'Ratio' columns
    df_melted = df.melt(id_vars=['Date'], var_name='Architecture', value_name='Ratio')

    # Define label mapping
    label_mapping = {
        "Low Power Heat Pump Water Heater": "HP (Rheem 120V)",
        "ESE Heat Pump Water Heater": "HP (120V) + Water Tank + Battery",
        "Heat Pump Water Heater": "HP (240V) + Resistive",
        "Electric Resistance Water Heater": "Electric Resistive (240V)",
        "Gas Water Heater": "Gas Water Heater",
        "ESE PCM Heat Pump Water Heater": "HP (120V) + PCM Tank + Battery",
        "Tankless Electric Water Heater": "Tankless Electric (240V)",
        "Gas Tankless Water Heater": "Tankless Gas"
    }
    
    desired_order = [
    "HP (Rheem 120V)",
    "HP (120V) + Water Tank + Battery",
    "HP (240V) + Resistive",
    "Electric Resistive (240V)",
    "Gas Water Heater",
    "HP (120V) + PCM Tank + Battery",
    "Tankless Electric (240V)",
    "Tankless Gas"
    ]

    # Apply mapping to Architecture column
    df_melted['Architecture'] = df_melted['Architecture'].map(label_mapping)

    # Create the horizontal box plot
    plt.figure(figsize=(14, 8))
    sns.boxplot(y='Architecture', x='Ratio', data=df_melted, order=desired_order, palette=palette)
    plt.subplots_adjust(left=0.3)

    # Optionally split labels across multiple lines
    #labels = plt.gca().get_yticklabels()
    #new_labels = [label.get_text().replace(' ', '\n') for label in labels]
    #plt.gca().set_yticklabels(new_labels)

    #plt.ylabel("Water Heater Architecture")
    plt.xlabel("Unmet to Usage Ratio")
    plt.ylabel("", labelpad=50)
    #plt.title("Unmet Events to Usage Events Ratio by Water Heater Architecture")
    plt.grid(axis='x', linestyle='--', alpha=0.7)

    axes_labels =  [
    "120V Heat Pump Water Heater",
    "120V Heat Pump + Water Tank + Li-Ion",
    "240V Heat Pump Water Heater",
    "240V Electric Resistive",
    "Gas Water Heater",
    "120V Heat Pump + PCM + Li-Ion",
    "240V Tankless Electric",
    "Tankless Gas"
    ]

    ax = plt.gca()
    ax.set_yticks(range(len(axes_labels)))
    ax.set_yticklabels(axes_labels)

    # Show plot
    plt.show()

# Example usage
csv_file = os.path.join(os.getcwd(), "ochre\\wh_tests\\results_analysis", "unmet_to_usage_ratios_apr3.csv")
plot_boxplot(csv_file)


