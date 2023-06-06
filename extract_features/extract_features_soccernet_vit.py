import timm
import numpy as np
import pandas as pd
import skvideo.io
import cv2
import torch
import os
import glob
import torch.nn as nn
import random
import pickle
import glob

DATA_ROOT = "./SoccerNetChunks"
# get all files in the directory
all_mp4_chunks = glob.glob(f'{DATA_ROOT}/*.mp4')


def get_video(video_path):
    video = skvideo.io.vread(video_path)
    frames = []
    for i in range(video.shape[0]):
        image = cv2.resize(video[i], (224, 224), interpolation=cv2.INTER_AREA)
        frames.append(image)
    frames = np.asarray(frames) / 255.0
    return frames

model = timm.create_model('vit_large_patch16_224_in21k', num_classes = 0, pretrained=True)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(device)
model.to(device)

#check if everything is working fine
x = torch.randn(2, 3, 224, 224).to(device)
y = model.forward_features(x)
print(y.shape)   #this should be of dimention [2,197,1024]


print('Total videos: ', len(all_mp4_chunks))
print('Total unique videos: ', len(set(all_mp4_chunks)))

random.shuffle(all_mp4_chunks) #helps if you want to run multiple instances parallelly

cnt = 0
for video_id in all_mp4_chunks:
    out_npy_name = video_id.split('/')[-1].split('.')[0]+'.npy'
    dest = f'./SoccerNetChunksFeatures/{out_npy_name}' #destination to save features
    if not os.path.exists(dest):
        video_fp = video_id
        if not os.path.exists(video_fp):
            print('Video not found :', video_id)
        if os.path.exists(video_fp):
            print('Processing video :', video_id)
            video = get_video(video_fp)
            video = torch.from_numpy(video.transpose([0, 3, 1, 2])).float()
            duration = 10
            print(cnt, video_id, video.shape, duration)
            features = np.zeros((duration+1, 197, 1024))
            for i in range(int(duration)):
                idx = int(video.shape[0] / duration * i)
                x = torch.unsqueeze(video[idx], 0).to(device)
                x = model.forward_features(x)
                features[i] = x.detach().cpu().numpy()
            x = model.forward_features(torch.unsqueeze(video[-1], 0).to(device))
            features[duration] = x.detach().cpu().numpy()
            np.save(dest, features)
            cnt += 1
