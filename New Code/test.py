import pandas as pd

# # Example DataFrame (Replace this with your actual DataFrame)
# data = {
#     'ColumnA': ['value1', 'value2', 'value1', 'value3', 'value2']
# }
# df = pd.DataFrame(data)
#
# # Get unique values from a column
# unique_values = df['ColumnA'].unique()
#
# # Create a dictionary with keys as the unique values and values as a sequence starting from 52
# starting_number = 52
# unique_dict = {value: starting_number + i for i, value in enumerate(unique_values)}
#
# # Display the dictionary
# print(unique_dict.get('value2'))

# networklan = "10.52.30.1"
# print(networklan[:-2]+"64")

import pandas as pd
from sklearn.cluster import KMeans

# Sample DataFrame loading (replace this with your actual DataFrame)
# df = pd.read_csv('your_file.csv')

# Example DataFrame creation
# data = {
#     'Sub Num': [1, 2, 3, 4, 5, 6],
#     'Sub Name': ['Sub A', 'Sub B', 'Sub C', 'D', 'E', 'F'],
#     'Sub ID': [101, 102, 103, 104, 105, 106],
#     'Longitude': [-104.99, -102.55, -100.75, -100.75, -100.75, -100.75],
#     'Latitude': [39.74, 38.25, 37.47, 37.47, 37.47, 37.47],
#     # ... include other columns as per your DataFrame
# }
# df = pd.DataFrame(data)
#
# # Selecting the columns for clustering
# X = df[['Latitude', 'Longitude']]
#
# # Number of clusters - This can be adjusted based on specific needs
# n_clusters = 3
#
# # Performing K-Means clustering
# kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X)
#
# # Adding the cluster labels (utility names) to the original DataFrame
# df['Utility Name'] = 'Utility ' + pd.Series(kmeans.labels_).astype(str)
#
# print(df)

# Correct initialization of an empty list
my_list = []

# Example data to iterate over
data = [1, 2, 3, 4, 5]

# Loop through the data
for item in data:
    print(item)
    # Append each item to the list
    my_list.append(item)

# Print the resulting list
print(my_list)


