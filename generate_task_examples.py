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
    assert isinstance(frames, list)
    framenames = [vid_id + '.' + f + '.jpg' for f in frames[:4]]
    framelinks = ['https://yuxixie.github.io/files/toy_examples/video_frames_dir/' + f for f in framenames]
    cmds = [f'<img src="{fl}" width="360" height="240">' for fl in framelinks]
    return '<td>' + '</td><td>'.join(cmds) + '</td>'


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


def get_task_cmd_abd(task, vid):
    label_cmd = '<li><strong>task type</strong> <strong><font color=DarkRed><code>ABDUCTIVE</code></font></strong></li>'

    end = task['observation']['end state']
    frames = ['https://yuxixie.github.io/files/toy_examples/video_frames_dir/' + vid + '.' + frm + '.jpg' for frm in task['observation']['background']]
    frames = ''.join([f'<td><img src="{frm}" width="360" height="240"></td>' for frm in frames])
    obv_cmd = '<li><strong>observation</strong><br/> <code>background</code> <br/>' \
        + f'<table>{frames}</table> <code>end state</code> {end} </li>'
    
    hyp = ''.join([f'<tr>{h}</tr>' for h in task['hypotheses']])
    hyp_cmd = f'<li><strong>hypotheses</strong><br/> <table>{hyp}</table> </li>'

    cmd = '<ul>' + label_cmd + obv_cmd + hyp_cmd + '</ul>'
    return cmd


def get_task_cmd_prd(task, vid):
    label_cmd = '<li><strong>task type</strong> <strong><font color=DarkGreen><code>PREDICTION</code></font></strong></li>'

    frames = ['https://yuxixie.github.io/files/toy_examples/video_frames_dir/' + vid + '.' + frm + '.jpg' for frm in task['premise']]
    frames = ''.join([f'<td><img src="{frm}" width="360" height="240"></td>' for frm in frames])
    bg_cmd = '<li><strong>premise</strong> <code>background</code> <br/>' \
        + f'<table>{frames}</table> </li>'
    
    hyp = task['hypothese']
    hyp_cmd = f'<li><strong>hypothese</strong> <code>activation</code> {hyp} </li>'

    prd = task['prediction']
    prd_cmd = f'<li><strong>prediction</strong> {prd} </li>'

    cmd = '<ul>' + label_cmd + bg_cmd + hyp_cmd + prd_cmd + '</ul>'
    return cmd


def get_task_cmd(task, vid):
    label = task['label']
    if label == 'abductive':
        return '<tr>' + get_task_cmd_abd(task, vid) + '</tr>'
    else:
        return '<tr>' + get_task_cmd_prd(task, vid) + '</tr>'


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
    
    task_cnt = sample['task']['count']
    task_brief = f'<strong><font color=BlueViolet>[Tasks]</font></strong> {task_cnt} reasoning tasks in total'
    tasks_cmd = task_brief + '<table>' + ''.join([get_task_cmd(task, sample['vid_seg_int']) for task in sample['task']['tasks']]) + '</table>'

    return ''.join(['<p>', head_cmd, iframe_cmd, tasks_cmd, '</p>'])


def load_data(filename):
    cmd_list = []
    with jsonlines.open(filename) as reader:
        for idx, sample in enumerate(reader):
            cmd = get_cmd(sample)
            _id = idx + 1
            vid = sample['vid_seg_int']
            outfile = f'tasks/task-{vid}.html'
            fileini = f'''---
title: "Visual-Linguistic Commonsense Reasoning Task"
author_profile: false
layout: case-study
---

'''
            write_file(fileini + cmd, outfile)

if __name__ == '__main__':
    filename = 'files/toy_examples/toy-task.jsonl'
    load_data(filename)