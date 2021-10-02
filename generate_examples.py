"""
<iframe src="https://www.youtube.com/embed/OO9kSxcT9Rg?start=790&end=793&version=3" scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width=450 height=300></iframe>
"""

import jsonlines
import json

COLOR_REL = {
    'Reaction To': '<td bgcolor=LightBlue><strong>Reaction</strong></td>',
    'Enables': '<td bgcolor=LemonChiffon><strong>Enables</strong></td>',
    'Causes': '<td bgcolor=LightPink><strong>Causes</strong>  </td>',
    'NoRel': '<td><strong>NoRel</strong></td>',
    'N/A': '<td><strong>N/A</strong></td>'
}

def write_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)

def get_cmd(sample):
    vid_seg_int = sample['vid_seg_int'].split('_')

    movie, clip, desc = sample['movie_name'], sample['clip_name'], sample['text']
    genres = [] if sample['genres'] == 'NA' else json.loads(sample['genres'].replace("'", '"'))
    genres = ''.join([f'<code>{gen}</code>' for gen in genres])
    head_cmd = f'<strong><font color=DodgerBlue>[Movie]</font>{movie}<font color=DodgerBlue>[Clip]</font>{clip}</strong>{genres}<br/>' \
        + f'<strong><font color=DodgerBlue>[Desc]</font></strong>{desc}<br/>' \
        + f'<strong><font color=YellowGreen>[10s-Clip]</font></strong> <br/>'

    iframe_cmd = f'<iframe src="https://www.youtube.com/embed/{vid_seg_int[1]}?start={vid_seg_int[3]}&end={vid_seg_int[4]}&version=3" ' \
        + f'scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width=600 height=400></iframe>'

    ev_table = '<strong><font color=BlueViolet>[Events]</font> 2s-long each </strong> <br/>' \
        + '<table><tr><td width="30"></td><td width="40"><strong>Rel-Ev3</strong></td><td><strong>Verb</td><td><strong>Narrative Semantic Roles</td></tr>'
    for evt, val in sample['caption'].items():
        cap, vb = val['complete'], val['verb']
        rel = COLOR_REL[val['EvRel']]
        event_ini = f'<tr><td><strong>{evt}</strong> </td>' + rel \
            + f'<td><strong>{vb}</strong></td>' \
            + f'<td>{cap}</td></tr>'
        ev_table += event_ini
    ev_table += '</table>'

    return ''.join(['<p>', head_cmd, iframe_cmd, ev_table, '</p>'])

def load_data(filename):
    cmd_list = []
    with jsonlines.open(filename) as reader:
        for idx, sample in enumerate(reader):
            cmd = get_cmd(sample)
            _id = idx + 1
            outfile = f'_exampletrain/example-train-{_id}.html'
            fileini = f'''---
title: "Hyp-VL Reasoning Example {_id}"
collection: exampletrain
---

'''
            write_file(fileini + cmd, outfile)

if __name__ == '__main__':
    filename = 'files/toy-train.jsonl'
    load_data(filename)