import os, sys
import numpy as np
import cv2
from PIL import Image
from multiprocessing import Pool
import argparse
from IPython import embed  # to debug
import skvideo.io
import scipy.misc
import imageio

def ToImg(raw_flow, bound):
    '''
    this function scale the input pixels to 0-255 with bi-bound

    :param raw_flow: input raw pixel value (not in 0-255)
    :param bound: upper and lower bound (-bound, bound)
    :return: pixel value scale from 0 to 255
    '''
    flow = raw_flow
    flow[flow > bound] = bound
    flow[flow < -bound] = -bound
    flow -= -bound
    flow *= (255 / float(2 * bound))
    return flow


def save_flows(flows, image, save_dir, num, bound):
    '''
    To save the optical flow images and raw images
    :param flows: contains flow_x and flow_y
    :param image: raw image
    :param save_dir: save_dir name (always equal to the video id)
    :param num: the save id, which belongs one of the extracted frames
    :param bound: set the bi-bound to flow images
    :return: return 0
    '''
    # rescale to 0~255 with the bound setting
    flow_x = ToImg(flows[..., 0], bound)
    flow_y = ToImg(flows[..., 1], bound)
    data_root = 'E:/datasets/UCF_Crime_100GB/Abuse/Abuse'
    # if not os.path.exists(os.path.join(data_root, new_dir, save_dir)):
    #     os.makedirs(os.path.join(data_root, new_dir, save_dir))
    if not os.path.exists(os.path.join(data_root, save_dir)):
        os.makedirs(os.path.join(data_root, save_dir))

    # save the image
    # save_img = os.path.join(data_root, new_dir, save_dir, 'img_{:05d}.jpg'.format(num))
    save_img = os.path.join(data_root, save_dir, 'img_{:05d}.jpg'.format(num))

    # scipy.misc.imsave(save_img, image)
    imageio.imsave(save_img, image)

    # save the flows
    # save_x = os.path.join(data_root, new_dir, save_dir, 'flow_x_{:05d}.jpg'.format(num))
    # save_y = os.path.join(data_root, new_dir, save_dir, 'flow_y_{:05d}.jpg'.format(num))
    save_x = os.path.join(data_root, save_dir, 'flow_x_{:05d}.jpg'.format(num))
    save_y = os.path.join(data_root, save_dir, 'flow_y_{:05d}.jpg'.format(num))
    flow_x_img = Image.fromarray(flow_x,mode="RGB")
    flow_y_img = Image.fromarray(flow_y,mode="RGB")
    # scipy.misc.imsave(save_x, flow_x_img)
    # scipy.misc.imsave(save_y, flow_y_img)
    imageio.imsave(save_x, flow_x_img)
    imageio.imsave(save_y, flow_y_img)
    return 0


def dense_flow(args):
    '''
    To extract dense_flow images
    :param augs:the detailed augments:
        video_name: the video name which is like: 'v_xxxxxxx',if different ,please have a modify.
        save_dir: the destination path's final direction name.
        step: num of frames between each two extracted frames
        bound: bi-bound parameter
    :return: no returns
    '''
    videos_root = 'E:/datasets/UCF_Crime_100GB/Abuse/Abuse'
    video_name, save_dir, step, bound = args
    video_path = os.path.join(videos_root, video_name)
    # video_path=os.path.join(videos_root,video_name.split('_')[1],video_name)

    # provide two video-read methods: cv2.VideoCapture() and skvideo.io.vread(), both of which need ffmpeg support

    # videocapture=cv2.VideoCapture(video_path)
    # if not videocapture.isOpened():
    #     print 'Could not initialize capturing! ', video_name
    #     exit()
    try:
        # 逐帧加载视频
        videocapture = skvideo.io.vread(video_path)
    except:
        print('{} 视频读入错误 ! '.format(video_name))
        return 0
    print(video_name)
    # if extract nothing, exit!
    if videocapture.sum() == 0:
        print('Could not initialize capturing', video_name)
        exit()
    len_frame = len(videocapture)
    frame_num = 0
    image, prev_image, gray, prev_gray = None, None, None, None
    num0 = 0
    while True:
        # frame=videocapture.read()
        if num0 >= len_frame:
            break
        frame = videocapture[num0]
        num0 += 1
        if frame_num == 0:
            image = np.zeros_like(frame)
            gray = np.zeros_like(frame)
            prev_gray = np.zeros_like(frame)
            prev_image = frame
            prev_gray = cv2.cvtColor(prev_image, cv2.COLOR_RGB2GRAY)
            frame_num += 1
            # to pass the out of stepped frames
            step_t = step
            while step_t > 1:
                # frame=videocapture.read()
                num0 += 1
                step_t -= 1
            continue

        image = frame
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        frame_0 = prev_gray
        frame_1 = gray
        ##default choose the tvl1 algorithm
        dtvl1 = cv2.createOptFlow_DualTVL1()
        # dtvl1 = cv2.createOptFlow_DualTVL1()
        # dtvl1 = cv2.optflow.DualTVL1OpticalFlow_create()
        # dtvl1 = cv2.DualTVL1OpticalFlow_create()
        # dtvl1 = cv2.createOptFlow_DualTVL1()

        flowDTVL1 = dtvl1.calc(frame_0, frame_1, None)
        save_flows(flowDTVL1, image, save_dir, frame_num, bound)  # this is to save flows and img.
        prev_gray = gray
        prev_image = image
        frame_num += 1
        # to pass the out of stepped frames
        step_t = step
        while step_t > 1:
            # frame=videocapture.read()
            num0 += 1
            step_t -= 1


def get_video_list():
    video_list = []
    for cls_names in os.listdir(videos_root):
        cls_path = videos_root
        # cls_path=os.path.join(videos_root,cls_names)
        for video_ in os.listdir(cls_path):
            video_list.append(video_)
    video_list.sort()
    return video_list, len(video_list)


def parse_args():
    parser = argparse.ArgumentParser(description="densely extract the video frames and optical flows")
    parser.add_argument('--dataset', default='ucf101', type=str, help='set the dataset name, to find the data path')
    # parser.add_argument('--data_root', default='E:/datasets/UCF_Crime_100GB/Abuse/Abuse.txt', type=str)
    parser.add_argument('--data_root', default='E:/datasets/UCF_Crime_100GB/Abuse/Abuse', type=str)
   # parser.add_argument('--new_dir', default='', type=str)
    parser.add_argument('--num_workers', default=4, type=int, help='num of workers to act multi-process')
    parser.add_argument('--step', default=1, type=int, help='gap frames')
    parser.add_argument('--bound', default=15, type=int, help='set the maximum of optical flow')
    parser.add_argument('--s_', default=0, type=int, help='start id')
    parser.add_argument('--e_', default=13320, type=int, help='end id')
    parser.add_argument('--mode', default='run', type=str, help='set \'run\' if debug done, otherwise, set debug')
    args = parser.parse_args()
    return args


if __name__ == '__main__':

    args = parse_args()
    # data_root = 'E:/datasets/UCF_I3D/Abuse'
    videos_root = 'E:/datasets/UCF_Crime_100GB/Abuse/Abuse'
    #test
    #videos_root = 'E:/datasets/UCF_I3D/Abuse'

    data_root = args.data_root
    # data_root=os.path.join(args.data_root,args.dataset)
    # videos_root=os.path.join(data_root,'videos')

    # specify the augments
    num_workers = args.num_workers
    step = args.step
    bound = args.bound
    s_ = args.s_
    e_ = args.e_
    # new_dir = args.new_dir
    mode = args.mode
    # get video list
    video_list, len_videos = get_video_list()
    video_list = video_list[s_:e_]

    #len_videos = min(e_ - s_, 13320 - s_)  # if we choose the ucf101
    #print('找到 {} 个视频.'.format(len_videos))
    flows_dirs = [video.split('.')[0] for video in video_list]
    print('获取视频列表完成! ')

    pool = Pool(num_workers)
    if mode == 'run':
        pool.map(dense_flow, zip(video_list, flows_dirs, [step] * len(video_list), [bound] * len(video_list)))
    else:  # mode=='debug
        dense_flow((video_list[0], flows_dirs[0], step, bound))


        # python denseflow.py --num_workers=4 --step=1 --bound=20 --mode=run --s_=0 --e_=3000