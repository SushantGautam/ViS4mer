import os
import json
import pandas as pd

directory = './SoccerNet/'

data = []
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith('-v2.json'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                json_data = json.load(f)
                url_local = json_data['UrlLocal']
                annotations = json_data['annotations']
                for annotation in annotations:
                    gameTime = annotation.get('gameTime', None)
                    label = annotation.get('label', None)
                    team = annotation.get('team', None)
                    data.append([url_local, gameTime, label, team])

df = pd.DataFrame(data, columns=['UrlLocal', 'gameTime', 'label', 'team'])

df[['League', 'year', 'GameName']] =  df['UrlLocal'].str.split('/', expand=True).iloc[:, :3]
df[['HalfNumber', 'gameTime']] = df['gameTime'].str.split('-', expand=True)
df['HalfNumber'] = df['HalfNumber'].str.strip()
df['gameTime'] = df['gameTime'].str.strip()
df['gameTime'] = pd.to_datetime(df['gameTime'], format='%M:%S').dt.time
df = df.drop('UrlLocal', axis=1)
print(df)

grouped_df = df.groupby('GameName')

result_df = pd.DataFrame()
for _, group in grouped_df:
    sorted_group = group
    sorted_group['gameTime'] = pd.to_datetime(sorted_group['gameTime'].astype(str))
    sorted_group['prev_event_time'] = sorted_group['gameTime'].shift(1)
    sorted_group['next_event_time'] = sorted_group['gameTime'].shift(-1)
    sorted_group['time_diff_before'] = (sorted_group['gameTime'] - sorted_group['prev_event_time']).dt.total_seconds().astype('Int64')
    sorted_group['time_diff_after'] = (sorted_group['next_event_time'] - sorted_group['gameTime']).dt.total_seconds().astype('Int64')
    result_df = pd.concat([result_df, sorted_group.iloc[:, 9:] ])
#concat result_df and df
df = pd.concat([df, result_df], axis=1)

#exclude events that where time_diff_before and time_diff_after are less than 5 seconds
df_5Plus = df[(df['time_diff_before'] > 5) & (df['time_diff_after'] > 5)]
#exclude events that where time_diff_before are less than 10 seconds
df_Bef10Plu = df[(df['time_diff_before'] > 10)]
#exclude events that where time_diff_after are less than 10 seconds
df_Aft10Plus = df[(df['time_diff_after'] > 10)]


import matplotlib.pyplot as plt
fig, ax = plt.subplots()
df_5Plus.hist( ax=ax, bins=120, column=['time_diff_before', 'time_diff_after'], figsize=(10, 5), range=(0, 120))
fig.savefig('example.png')

# give number of event of each label in each df_5Plus 
df_5Plus.groupby(['label']).size()