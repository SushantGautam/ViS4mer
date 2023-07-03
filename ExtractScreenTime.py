import json
import os
import time

def extract_screen_time_from_json(file_path, calcDiff=False):
    with open(file_path, 'r') as file:
        annotations = json.load(file)['annotations']

    events = []
    recording, followUp = False, False
    for event in reversed(annotations):
        if not recording and event['replay'] == 'replay':
            recording = True
            gameTime = f"{event['link']['half']} - {event['link']['time']}"
            endTime = event['gameTime']
            eventName = event['link']['label']
        elif recording:
            if event['replay'] == 'real-time':
                recording = False
            else:
                followUp = True
            startTime = event['gameTime']
            all_events = {
                'gameTime': gameTime,
                'startTime': startTime,
                'endTime': endTime,
                'followUp': followUp,
                'eventName': eventName
            }
            events.append(all_events)
            followUp = False

    events = events[::-1]
    for cr_evt, nx_evt in zip(events, events[1:]):
        if cr_evt['gameTime'] == nx_evt['gameTime'] and cr_evt['eventName'] == nx_evt['eventName'] and cr_evt['endTime'] == nx_evt['endTime']:
            cr_evt['endTime'] = nx_evt['startTime']

    for event in events:
        end_time = list(map(int, event['endTime'].replace('-', ':').split(':')))
        start_time = list(map(int, event['startTime'].replace('-', ':').split(':')))
        game_time = list(map(int, event['gameTime'].replace('-', ':').split(':')))
        time_diff = (end_time[1] - start_time[1]) * 60 + (end_time[2] - start_time[2])
        replay_delay =(start_time[1] - game_time[1]) * 60 + (start_time[2] - game_time[2])

        if calcDiff:
            event.update({'timeDiff': time_diff, 'replayDelay': replay_delay})
            
        event['eventName']= event.pop('eventName')
    return events


file_path = './SoccerNet/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley/Labels-cameras.json'
events = extract_screen_time_from_json(file_path, calcDiff=True)

for event in events:
    print(event)