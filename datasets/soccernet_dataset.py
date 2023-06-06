import torch
import os
import numpy as np
import random
import pandas as pd
from torch.utils.data import Dataset, DataLoader

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.device_count() > 0:
        torch.cuda.manual_seed_all(seed)
set_seed(1112)

game_events = {
    'Foul': 0,
    'Balloutofplay': 1,
    'Indirectfree-kick': 2,
    'Clearance': 3,
    'Shotsontarget': 4,
    'Corner': 5,
    'Substitution': 6,
    'Throw-in': 7
}


DATA_ROOT ="./SoccerNetChunksFeatures"
# get all files in the directory with full path
files = [os.path.join(DATA_ROOT, f) for f in os.listdir(DATA_ROOT) if os.path.isfile(os.path.join(DATA_ROOT, f))]

class CustomDataset(Dataset):
    def __init__(self, args, split):
        self.args = args
        self.split = split

        self.videos = []
        self.labels = []
        self.starts = []
 
        for feature_path in files:
            video_id = feature_path.split('/')[-1].split('.')[0]
            # 2014-11-04-22-45Arsenal3-3Anderlecht_2_00_08_07|Throw-in.npy
            print(video_id, feature_path)
            label = game_events[video_id.split('|')[-1].split('.')[0]]
            duration = 9
            self.videos.append(video_id)
            self.starts.append(0)
            self.labels.append(label)

            for start in range(1, duration-args.l_secs+1):
                self.videos.append(video_id)
                self.starts.append(start)
                self.labels.append(label)

        print('Total videos in ', split, len(set(self.videos)))
        print('Total spans ', split, len(self.videos))
        print('Total labels ', split, len(set(self.labels)))

    def __len__(self):
        if self.split == 'train':
            return len(set(self.videos))
        else:
            return len(self.videos)

    def __getitem__(self, idx):
        if self.split == 'train':
            idx = random.randint(0, len(self.videos)-1)

        if self.args.feature_type == 'vit_spatial':
            video_features = np.load(f'{DATA_ROOT}/{self.videos[idx]}.npy')
            x = np.zeros((self.args.l_secs, 197, 1024))
            for i in range(self.starts[idx], min(self.starts[idx] + self.args.l_secs, video_features.shape[0])):
                x[i - self.starts[idx]] = video_features[i]
            x = np.reshape(x,(x.shape[0]* x.shape[1], 1024))

        #you can add support for other types of features smilarly

        return self.videos[idx], x, self.labels[idx]