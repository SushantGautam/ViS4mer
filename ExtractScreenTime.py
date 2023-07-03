import json

import os# clear screen
os.system('cls' if os.name == 'nt' else 'clear')
def extract_common_labels(annotations):
    common_labels = []
    replay_labels = []

    for annotation in annotations:
        print("annotation", annotation)
        # change_type = annotation['change_type']
        replay = annotation.get('replay', '')
        print("replay", replay, "replay_labels", replay_labels)
        if replay == 'replay':
            if replay_labels and any([label['link']['time']!= annotation['link']['time'] for label in replay_labels]):
                replay_label = replay_labels[0]
                common_labels.append({
                    'label': replay_label,
                    'startTime': replay_labels[0]['gameTime'],
                    'endTime': annotation['gameTime']
                })
                replay_labels = []
                replay_labels.append(annotation)
            else:
                replay_labels.append(annotation)
        elif replay == 'real-time' and replay_labels and all([label['link']['time']== replay_labels[0]['link']['time'] for label in replay_labels]):
            replay_label = replay_labels[0]
            common_labels.append({
                'label': replay_label,
                'startTime': replay_labels[0]['gameTime'],
                'endTime': annotation['gameTime']
            })
            replay_labels = []

    return common_labels

# Example usage
# Assuming your dataset is stored in a file called 'dataset.json'
with open('./SoccerNet/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley/Labels-cameras.json', 'r') as file:
    dataset = json.load(file)['annotations']

# common_labels = extract_common_labels(dataset)

# parsed_common_labels = []
# for label in common_labels:
#     endTime = label['endTime']
#     startTime = label['startTime']
#     parsed_common_labels.append({
#         'label': label['label']['link']['label'],
#         'eventTime': label['label']['link']['time'],
#         'startTime': label['startTime'],
#         'endTime': endTime,
#         # subtracting startTime from endTime to get the time difference
#         'timeDiff': (int(endTime.split('-')[0]) - int(startTime.split('-')[0])) * 45 * 60 + (int(endTime.split('-')[1].split(':')[0]) - int(startTime.split('-')[1].split(':')[0])) * 60 + (int(endTime.split('-')[1].split(':')[1]) - int(startTime.split('-')[1].split(':')[1]))
#     })


# # Print the extracted common labels in single line
# for label in parsed_common_labels:
#     print(
#         label['label'], "-", label['eventTime'],
#            "\t\tstartTime", label['startTime'], "\t\tendTime", label['endTime'], "\t\ttimeDiff", label['timeDiff'])


# invert dataset

recording = False

gameTime, startTime, endTime, eventName, followUp = None, None, None, None, False    
all_events=[]

for events in dataset[::-1]:
    if recording ==False and events['replay'] == 'replay':
        recording = True
        gameTime=events['link']['half']+" - "+ events['link']['time'] #sample:  '2- 23:09', time
        endTime = events['gameTime']
        eventName = events['link']['label']

    elif recording ==True:
        if events['replay'] == "real-time":
            recording = False
            
        else:
            followUp = True
            
        startTime = events['gameTime'] # sample: 'startTime': '2 - 17:05',, gameHalf - time
        all_events.append({"gameTime": gameTime, "startTime": startTime, "endTime": endTime,
                        #    "timeDiff": timeDiff,
                        #    "replayDelay": replayDelay,                            
                           "followUp": followUp,
                           "eventName": eventName, 
                           })
        followUp = False


events= all_events[::-1]

# if gameTime, eventName and endTime is same as the next event in events, then set its endTime to the next event's startTime
for i in range(len(events) - 1):
    current_event = events[i]
    next_event = events[i + 1]

    if (
        current_event["gameTime"] == next_event["gameTime"]
        and current_event["eventName"] == next_event["eventName"]
        and current_event["endTime"] == next_event["endTime"]
    ):
        current_event["endTime"] = next_event["startTime"]


# add timeDiff and replayDelay
for i in range(len(events)):
    #diff between start and end time
    timeDiff= (int(events[i]['endTime'].split('-')[0]) - int(events[i]['startTime'].split('-')[0])) * 45 * 60 + (int(events[i]['endTime'].split('-')[1].split(':')[0]) - int(events[i]['startTime'].split('-')[1].split(':')[0])) * 60 + (int(events[i]['endTime'].split('-')[1].split(':')[1]) - int(events[i]['startTime'].split('-')[1].split(':')[1]))

    # Calculate the difference between gameTime and startTime
    replayDelay = (int(events[i]['startTime'].split('-')[0]) - int(events[i]['gameTime'].split('-')[0])) * 45 * 60 + (int(events[i]['startTime'].split('-')[1].split(':')[0]) - int(events[i]['gameTime'].split('-')[1].split(':')[0])) * 60 + (int(events[i]['startTime'].split('-')[1].split(':')[1]) - int(events[i]['gameTime'].split('-')[1].split(':')[1]))

    events[i]['timeDiff'] = timeDiff
    events[i]['replayDelay'] = replayDelay
    # make eventName key at last
    events[i]['eventName'] = events[i].pop('eventName')

for event in events:
    print(event)