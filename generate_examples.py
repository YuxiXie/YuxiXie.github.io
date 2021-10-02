"""
<iframe src="https://www.youtube.com/embed/OO9kSxcT9Rg?start=790&end=793&version=3" scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width=450 height=300></iframe>
"""

import jsonlines

def get_cmd(sample):
    vid_seg_int = sample['vid_seg_int'].split('_')

    iframe_cmd = f'<iframe src="https://www.youtube.com/embed/{vid_seg_int[1]}?start={vid_seg_int[3]}&end={vid_seg_int[4]}&version=3" ' \
        + f'scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width=600 height=400></iframe>'

    return {
        'video_id': vid_seg_int[1],
        'start': vid_seg_int[3], 'end': vid_seg_int[4],
        'movie_name': sample['movie_name'], 'genres': sample['genres'],
        'clip_name': sample['clip_name'], 'text': sample['text'],
        'events': sample['Events']
    }

def load_data(filename):
    with jsonlines.open(filename) as reader:
        for sample in reader:
            cmd_dict = get_cmd(sample)