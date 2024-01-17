# import pandas as pd
# from sklearn.cluster import KMeans
#
# # Example DataFrame creation (replace with your actual DataFrame)
# data = {
#     'Sub Num': [1, 2, 3],
#     'Sub Name': ['Sub A', 'Sub B', 'Sub C'],
#     'Sub ID': [101, 102, 103],
#     'Longitude': [-104.99, -102.55, -100.75],
#     'Latitude': [39.74, 38.25, 37.47],
#     # ... include other columns as per your DataFrame
# }
# df = pd.DataFrame(data)
#
# # Selecting the columns for clustering
# X = df[['Latitude', 'Longitude']]
#
# # Number of clusters
# n_clusters = 3
#
# # Performing K-Means clustering
# kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(X)
#
# # Extracting the centroids
# centroids = kmeans.cluster_centers_
#
# # Adding the cluster labels (utility names) to the original DataFrame
# df['Utility Name'] = 'Utility ' + pd.Series(kmeans.labels_).astype(str)
#
# # Get unique utility names and their corresponding centroids
# unique_utilities = df['Utility Name'].unique()
# utility_centroids = {name: centroids[int(name.split(' ')[1])] for name in unique_utilities}
#
# # Create a dictionary with utility names, starting numbers, and centroids
# starting_utl_number = 52
# utility_dict = {
#     name: {
#         'id': starting_utl_number + i,
#         'latitude': utility_centroids[name][0],
#         'longitude': utility_centroids[name][1]
#     }
#     for i, name in enumerate(unique_utilities)
# }
#
# print(utility_dict.get('Utility 1').get('id'))
#
# for key, val in utility_dict.items():
#     # Constructing the base part of the ID
#     util_label = f"Region.{key}"
#     utl_ID = val.get('id')
#     print(util_label)
#     print(utl_ID)
# # for utility_name, info in utility_dict.items():
# #     centroid = info['centroid']
# #     latitude = centroid[0]
# #     longitude = centroid[1]
# #     print(f"{utility_name}: Latitude = {latitude}, Longitude = {longitude}")

def extract_word_from_string(input_string, position):
    """
    Extracts a word from a given position in a string.

    Parameters:
    input_string (str): The string to extract the word from.
    position (int): The position of the word to extract, starting from 0.

    Returns:
    str: The extracted word.
    """
    words = input_string.split('.')
    if position < len(words):
        return words[position].split(' ')[0]
    else:
        return "Position out of range"


# Example usage
input_string = 'Utility 0.Bus 1..Firewall 1'
position = 3  # For extracting 'Firewall' which is the 3rd word (position index starts from 0)
extracted_word = extract_word_from_string(input_string, position)

print(extracted_word)

