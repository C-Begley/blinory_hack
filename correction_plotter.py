'''
Copyright (C) 2025

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
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

