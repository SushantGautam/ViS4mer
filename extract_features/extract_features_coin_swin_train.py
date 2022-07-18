import json
import os
import sys
import glob
import skvideo.io
from moviepy.editor import *
import numpy as np
import torch
import cv2
import random
from mmaction.apis import init_recognizer, inference_recognizer
from mmaction.models import build_model
from einops import rearrange, reduce, repeat

config_file = 'Video-Swin-Transformer/configs/recognition/swin/swin_base_patch244_window877_kinetics600_22k.py'
# # download the checkpoint from model zoo and put it in `checkpoints/`
checkpoint_file = 'Video-Swin-Transformer/checkpoints/swin_base_patch244_window877_kinetics600_22k.pth'
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = init_recognizer(config_file, checkpoint_file, device=device)

f = open('../data/COIN/COIN.json')
data = json.load(f)['database']

files = glob.glob(f'/playpen-storage/mmiemon/lvu/data/COIN/videos/*/*.mp4')
random.shuffle(files)

for cnt, file in enumerate(files):
    video_id = file.split('/')[-1].split('.')[0]
    if video_id in ['AfiVmAjfTNs', 'cjwtcDKTQM8']:
        continue

    dest_mean = f'/playpen-storage/mmiemon/lvu/data/COIN/features/temporal_mean_pooling/{video_id}.npy'

    if os.path.exists(dest_mean):
        continue

    if data[video_id]['subset'] == 'training':
        duration = data[video_id]['end'] - data[video_id]['start']
        clip = VideoFileClip(file)
        n_frames = int(duration * clip.fps)
        n_segments = 256
        segment_length = 32

        if n_frames < (n_segments + segment_length):
            starts = [i for i in range(n_frames - segment_length)]
        else:
            step = (n_frames - segment_length) / float(n_segments)
            starts = np.arange(0, n_frames - segment_length, step=step)

        mean_features = []
        for start in starts:
            start = int(start)
            print('training video ', cnt, '/', len(files), video_id, 'start', start, '/', n_frames)

            frames = []
            for i in range(start, start + segment_length):
                image = clip.get_frame(data[video_id]['start']+(i / clip.fps))
                image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)
                frames.append(image)
            frames = np.asarray(frames) / 255.0
            frames = torch.from_numpy(frames.transpose([3, 0, 1, 2])).float()
            frames = torch.unsqueeze(frames, 0)
            features = torch.squeeze(model.extract_feat(frames.to(device))).detach().cpu().numpy()

            mean = reduce(features, 'c t h w -> c h w', 'mean')
            mean = rearrange(mean, 'c h w-> (h w) c')
            mean_features.append(mean)

        mean_features = np.asarray(mean_features)

        np.save(dest_mean, mean_features)

