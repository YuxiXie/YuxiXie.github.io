import jsonlines
import json

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


def frame_cmd(frames, vid_id):
    if isinstance(frames, list):
        framename = frames[0]
    else:
        return ''
    framename = vid_id + '.' + framename + '.jpg'
    framelink = 'https://yuxixie.github.io/files/toy_examples/frames/' + framename
    cmd = f'<img src="{framelink}" width="480" height="360">'
    return cmd


def srl_process(srl):
    spans = []
    for k, v in srl.items():
        text, desc = v['text'], v['desc']
        color = COLOR_SRL[k]
        txt_cmd = f'<font color={color} size="4">{text}</font>'
        if desc and len(desc) > 2:
            txt_cmd += f' {desc}'
        spans.append('<u>' + txt_cmd + '</u>')
    return '  '.join(spans)


def get_cmd(sample):
    vid_seg_int = sample['vid_seg_int'].split('_')

    movie, clip, desc = sample['movie_name'], sample['clip_name'], sample['text']
    genres = [] if sample['genres'] == 'NA' else json.loads(sample['genres'].replace("'", '"'))
    genres = ''.join([f'<code>{gen}</code>' for gen in genres])
    head_cmd = f'<strong><font color=DodgerBlue>[Movie]</font> {movie}  <font color=DodgerBlue>[Clip]</font> {clip} </strong> {genres}<br/>' \
        + f'<strong><font color=DodgerBlue>[Desc]</font></strong> {desc}<br/>' \
        + f'<strong><font color=YellowGreen>[10s-Clip]</font></strong> <br/>'

    iframe_cmd = f'<iframe src="https://www.youtube.com/embed/{vid_seg_int[1]}?start={vid_seg_int[3]}&end={vid_seg_int[4]}&version=3" ' \
        + f'scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width="600" height="400"></iframe> <br/>'

    ev_table = '<strong><font color=BlueViolet>[Events]</font></strong> 2s-long each <br/>' \
        + '<table><tr><td width="30"></td><td width="40"><strong>RelToEv3</strong></td><td><strong>Frame</strong></td>' \
        + '<td><strong>Narrative Semantic Roles</strong></td></tr>'
    for evt, val in sample['events'].items():
        frame_info, srl_text = frame_cmd(val['Frames'], sample['vid_seg_int']), srl_process(val['SRL'])
        rel = val['EvRel'] if val['EvRel'] else 'N/A'
        rel = COLOR_REL[rel]
        event_ini = f'<tr><td><strong>{evt}</strong> </td>' + rel \
            + f'<td>{frame_info}</td>' \
            + f'<td>{srl_text}</td></tr>'
        ev_table += event_ini
    ev_table += '</table>'

    return ''.join(['<p>', head_cmd, iframe_cmd, ev_table, '</p>'])

def load_data(filename):
    cmd_list = []
    with jsonlines.open(filename) as reader:
        for idx, sample in enumerate(reader):
            cmd = get_cmd(sample)
            _id = idx + 1
            outfile = f'_example/example-train-{_id}.html'
            fileini = f'''---
title: "Hyp-VL Reasoning Example Train {_id}"
collection: example
---

'''
            write_file(fileini + cmd, outfile)

if __name__ == '__main__':
    filename = 'files/toy_examples/train.jsonl'
    load_data(filename)