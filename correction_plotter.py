import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

df = pd.read_csv('corrections.csv')

if df.shape[1] == 5:  # If there are exactly 4 columns
    try:
        time_data = pd.to_datetime(df.iloc[:, 0])
        values = df.iloc[:, 1:]  # Get the remaining 3 columns
        x_label = 'Time'
    except:
        print("failed to parse first column as time")
        exit()
else:
    print("Unexpected number of columns")
    exit()

plt.figure(figsize=(10, 6))

column_names = [
    "Suggested Correction X",
    "Suggested Correction Y",
    "Smoothed Correction X",
    "Smoothed Correction Y",
        ]

for i, column in enumerate(values.columns):
    plt.plot(time_data, values[column], label=column_names[i])

plt.xlabel(x_label)
plt.ylabel('steering %')
plt.title('Corrections')
plt.legend()
plt.grid(True)

plt.xticks(rotation=45)

# Show the plot
plt.tight_layout()
plt.show()

