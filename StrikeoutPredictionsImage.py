import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from datetime import date
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Read the CSV data
df = pd.read_csv('pitcher_strikeout_predictions.csv')

# Round specified columns to 2 decimal places
df['Expected Innings'] = df['Expected Innings'].round(2)
df['Predicted Strikeouts'] = df['Predicted Strikeouts'].round(2)

# Convert probabilities to percentages, handling NaN values, without rounding
def to_percentage(x):
    if pd.isna(x):
        return ''
    else:
        return f"{x * 100:.2f}%"

df['Probability Over'] = df['Probability Over'].apply(to_percentage)
df['Alternate Probability Over'] = df['Alternate Probability Over'].apply(to_percentage)

# Select columns to display
columns_to_display = ['Pitcher', 'Team', 'Expected Innings', 'Predicted Strikeouts', 'Book Line', 'Probability Over', 'Alternate Line', 'Alternate Probability Over']

# Create a figure and axis
fig, (ax_title, ax, ax_key) = plt.subplots(3, 1, figsize=(22, 16), gridspec_kw={'height_ratios': [1, 4, 1]})

# Hide axes
ax_title.axis('off')
ax.axis('off')
ax_key.axis('off')

# Create the table
table = ax.table(cellText=df[columns_to_display].values,
                 colLabels=columns_to_display,
                 cellLoc='center',
                 loc='center')

# Set table properties
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.3, 2.2)  # Increased vertical scale to fit text

def get_color(prob):
    try:
        if isinstance(prob, str):
            prob = float(prob.strip('%'))
        elif isinstance(prob, (float, np.float64)):
            prob *= 100  # Convert to percentage
        else:
            return 'white'
        
        if 60 < prob < 66:
            return '#90EE90'  # Light green
        elif prob >= 66:
            return '#32CD32'  # Dark green
        elif 40 <= prob < 50:
            return '#FFA07A'  # Light red
        elif prob < 40:
            return '#FF6347'  # Tomato (lighter shade of red)
        else:
            return 'white'
    except ValueError:
        return 'white'

# Apply colors to the table and set bold font
for row in range(len(df) + 1):  # Include header row
    for col in range(len(columns_to_display)):
        cell = table.get_celld()[row, col]
        cell.set_text_props(weight='bold')
        cell.set_edgecolor('none')  # Remove cell borders
        
        if row == 0:  # Header row
            cell.set_facecolor('#E6E6E6')  # Light gray background for header
        elif col in [4, 5, 6, 7]:  # Columns to color
            if col in [4, 5]:  # Book Line and Probability Over
                prob = df.iloc[row-1]['Probability Over']
            else:  # Alternate Line and Alternate Probability Over
                prob = df.iloc[row-1]['Alternate Probability Over']
            color = get_color(prob)
            cell.set_facecolor(color)

# Add color key
colors = ['#90EE90', '#32CD32', '#FFA07A', '#FF6347']
labels = ['Good Over', 'Stronger Over', 'Strong Under', 'Stronger Under']
for i, (color, label) in enumerate(zip(colors, labels)):
    rect = Rectangle((0.1 + i*0.2, 0.5), 0.05, 0.05, facecolor=color, edgecolor='black')
    ax_key.add_patch(rect)
    ax_key.text(0.1 + i*0.2 + 0.07, 0.525, label, va='center')

ax_key.text(0.1, 0.7, 'Color Key:', fontweight='bold')

# Add title and logo
today = date.today().strftime("%B %d, %Y")
ax_title.text(0.5, 0.6, f"SlideSports MLB Strikeout Predictions - {today}", fontsize=16, fontweight='bold', ha='center')
ax_title.text(0.5, 0.3, "@Slide__Sports on X!", fontsize=12, ha='center')

# Add logo
logo = plt.imread('SlideLogo.jpeg')
imagebox = OffsetImage(logo, zoom=0.15)
ab = AnnotationBbox(imagebox, (0.95, 0.6), frameon=False)
ax_title.add_artist(ab)

# Adjust layout and save the figure
plt.tight_layout()
plt.savefig('pitcher_strikeout_predictions_table.png', dpi=300, bbox_inches='tight')
plt.close()

print("Table image has been saved as 'pitcher_strikeout_predictions_table.png'")