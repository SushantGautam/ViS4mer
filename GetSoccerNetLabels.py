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
    sorted_group['time_diff_before'] = (sorted_group['gameTime'] - sorted_group['prev_event_time']).dt.total_seconds().astype('Int64', errors='ignore')
    sorted_group['time_diff_after'] = (sorted_group['next_event_time'] - sorted_group['gameTime']).dt.total_seconds().astype('Int64', errors='ignore')
    result_df = pd.concat([result_df, sorted_group.iloc[:, 9:] ])


#concat result_df and df
df = pd.concat([df, result_df], axis=1)

#exclude events that where time_diff_before and time_diff_after are less than 5 seconds
df_5Plus = df[(df['time_diff_before'] > 5) & (df['time_diff_after'] > 5)]
# find most occuring 8 labels and exclude other labels
most_occuring_labels = df_5Plus.groupby(['label']).size().sort_values(ascending=False).head(8).index
df_5Plus = df_5Plus[df_5Plus['label'].isin(most_occuring_labels)]

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


def find_consecutive_event_counts(events_list):
    consecutive_event_counts = {}
    for sublist in events_list:
        for i in range(len(sublist) - 1):
            consecutive_event = tuple(sublist[i:i+2])
            if consecutive_event in consecutive_event_counts:
                consecutive_event_counts[consecutive_event] += 1
            else:
                consecutive_event_counts[consecutive_event] = 1
    sorted_counts = sorted(consecutive_event_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_result = {k: v for k, v in sorted_counts}
    return sorted_result

# study consecutive events 
# all_events = list(df[(df['time_diff_before'] > 20) & (df['time_diff_after'] > 20)].groupby(['GameName'])['label'].apply(list).values)
# find_consecutive_event_counts(all_events)

import datetime

# create df_edit with gameName, label, cropStart (gameTime - 5 seconds), cropEnd (gameTime + 5 seconds)
df_edit = df_5Plus[['League', 'year', 'GameName', 'label', 'gameTime','HalfNumber']]
current_date = datetime.datetime.now().date()
df_edit['cropStart'] = [datetime.datetime.combine(current_date, time) - datetime.timedelta(seconds=5) for time in df_edit['gameTime']]
df_edit['cropStart'] = df_edit['cropStart'].dt.time
df_edit['cropEnd'] = [datetime.datetime.combine(current_date, time) + datetime.timedelta(seconds=5) for time in df_edit['gameTime']]
df_edit['cropEnd'] = df_edit['cropEnd'].dt.time
# create finalName column from GameName space deleted, and with gameTime
df_edit['finalName'] = df_edit['GameName'].str.replace(' ', '')+'_'+df_edit['HalfNumber']+"_"+df_edit['gameTime'].astype(str).str.replace(':', '_') +"|"+ df_edit['label'].str.replace(' ', '')+'.mp4'
df_edit['UrlLocal'] = df_edit['League']+'/'+df_edit['year']+'/'+df_edit['GameName']+ '/' + df_edit['HalfNumber']+"_224p.mkv"
# mkv  to mp4 and also crop video
df_edit['ffmpeg_code'] = "ffmpeg  -n  -i './SoccerNet/"+df_edit['UrlLocal']+"' -ss "+df_edit['cropStart'].apply(lambda x: str(x))+" -to "+df_edit['cropEnd'].apply(lambda x: str(x))+" -c copy './SoccerNetChunks/"+ df_edit['finalName']+"'"
# execute ffmpeg_code
# df_edit['ffmpeg_code'].apply(lambda x: os.system(x))
df_edit
# ls -l SoccerNetChunks/ | egrep -c '^-'