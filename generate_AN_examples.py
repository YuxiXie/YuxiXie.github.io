import jsonlines
import json
import os
import math

COLOR_REL = {
    'Reaction To': '<td bgcolor=LightBlue><strong>Reaction</strong></td>',
    'Enables': '<td bgcolor=LemonChiffon><strong>Enables</strong></td>',
    'Causes': '<td bgcolor=LightPink><strong>Causes</strong>  </td>',
    'NoRel': '<td><strong>NoRel</strong></td>',
    'N/A': '<td>N/A</td>'
}

COLOR_SRL = {
    'Arg0': 'DarkGreen', 
    'Verb': 'DarkRed', 
    'Arg1': 'DarkBlue', 
    'Arg2': 'Goldenrod', 
    'Arg3': 'DarkCyan', 
    'Arg4': 'DarkCyan', 
    'ArgM': 'DarkViolet', 
    'Scene of the Event': 'MediumVioletRed'
}


def write_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)


def get_caption(cap, i, ids):

    def digital(time):
        minute = time // 60
        second = time % 60
        return f'{minute:02d}:{second:02d}'

    _id = i + 1
    color = 'LemonChiffon' if i in ids else 'White'
    sent = cap['sentence']
    s, e = math.floor(cap['timestamp'][0]), math.ceil(cap['timestamp'][1])
    dur = e - s
    s, e = digital(s), digital(e)
    cap_cmd = f'<td>{_id}</td><td>{s}</td><td>{e}</td><td>{dur}s</td><td bgcolor={color}>{sent}</td>'
    return cap_cmd


def get_cmd(sample):
    vid = sample['vid']
    vid_seg_int = vid.split('_')

    head_cmd = f'<strong><font color=YellowGreen>[Video-Clip]</font></strong> <br/>'

    iframe_cmd = f'<iframe src="https://www.youtube.com/embed/{vid_seg_int[1]}?start={vid_seg_int[3]}&end={vid_seg_int[4]}&version=3" ' \
        + f'scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width="600" height="400"></iframe> <br/>'

    ids = sample['captions']['selected_ids']
    sents = sample['captions']['captions']
    captions = '<tr>' + '</tr><tr>'.join([get_caption(sent, i, ids) for i, sent in enumerate(sents)]) + '</tr>'
    cap_cmd = f'<strong><font color=DodgerBlue>[Desc]</font></strong> <br/>' \
        + '<table><tr><td width="30"><strong>ID</strong></td><td width="30"><strong>StartPoint</strong></td>' \
        + f'<td width="30"><strong>EndPoint</strong><td width="30"><strong>Duration</strong></td></td><td><strong>Sentence</strong></td></tr>{captions}</table>'


    return ''.join(['<p>', head_cmd, iframe_cmd, cap_cmd, '</p>'])


def load_data(filename):
    cmd_list = []
    with jsonlines.open(filename) as reader:
        for idx, sample in enumerate(reader):
            cmd = get_cmd(sample)
            _id = idx + 1
            outfile = f'_example/example-actynet-{_id:02d}.html'
            fileini = f'''---
title: "ActyNet Example {_id:02d}"
collection: example
---

'''
            write_file(fileini + cmd, outfile)

if __name__ == '__main__':
    filename = 'files/actynet-toy.jsonl'
    load_data(filename)