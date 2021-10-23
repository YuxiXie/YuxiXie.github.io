import json
import codecs

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


def get_task_cmd(task, sample, tid):
    tid = tid + 1
    task = task.split('-')
    vid_in, txt_in, txt_out = ' + '.join(task[0]), task[1], task[2]

    label = 'abductive' if int(txt_out[0]) < int(txt_in[0]) else 'predictive'
    label_color = 'DarkGreen' if label == 'abductive' else 'DarkRed'
    label_cmd = f'<strong><font size="4"> task {tid} </font></strong>' \
        + f'<li><strong>[task type]</strong> <font color={label_color}>{label}</font> </li>'

    pm_cmd = f'<li><strong><font color=YellowGreen>[premise]</font></strong> <code>{vid_in}</code> <br/>'

    rst = ' '.join([sample[f'ev{x}']['desc'] for x in txt_in])
    rst_cmd = f'<li><strong><font color=DodgerBlue>[result]</font></strong> <code>(observed result)</code> {rst} </li>'
    
    all_answers = []
    for x in txt_out:
        ans = sample[f'ev{x}']['desc']
        if ans not in all_answers:
            all_answers += [ans]
    ans = ''.join([
        f'<tr><td bgcolor=LemonChiffon><strong><font size="4">internal_{i}</font></strong></td>' \
        + f'<td bgcolor=LemonChiffon><font size="4">{a}</font></td></tr>' for i, a in enumerate(all_answers, 1)
    ])
    
    qu_ans = f'<table>{ans}</table>'
    qa_cmd = f'<li><strong><font color=BlueViolet>[Abductive]</font></strong><br/> {qu_ans} </li>'

    return ' '.join(['<tr>', label_cmd, pm_cmd, rst_cmd, qa_cmd, '</tr>'])


def get_cmd(sample, annot_id):
    vid_seg_int = sample['vid_seg_int'].split('_')
    vid = '_'.join(vid_seg_int[1:-3])

    movie, clip, desc = sample['movie_name'], sample['clip_name'], sample['clip_desc']
    genres = sample['genres'] if isinstance(sample['genres'], list) else []
    genres = ''.join([f'<code>{gen}</code>' for gen in genres])
    head_cmd = f'<strong><font color=DodgerBlue>[Movie]</font> {movie}  <font color=DodgerBlue>[Clip]</font> {clip} </strong> {genres}<br/>' \
        + f'<strong><font color=DodgerBlue>[Desc]</font></strong> {desc}<br/>'

    start, end = vid_seg_int[-2], int(vid_seg_int[-2]) + 4
    iframe_cmd = '<strong><font color=YellowGreen>[Premise]</font></strong> You can also refer to the thumbnail (for replaying: please refresh the page). <br/>' \
        + f'<iframe src="https://www.youtube.com/embed/{vid}?start={start}&end={end}&version=3" ' \
        + 'scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width="900" height="600"></iframe> <br/>'
    
    sample = sample['annots'][annot_id]
    tasks, task_cnt = sample['tasks'], len(sample['tasks'])
    task_brief = f'<strong><font color=BlueViolet>[Tasks]</font></strong> {task_cnt} reasoning task(s) in total <br/><br/>'
    tasks_cmd = task_brief + '<br/><hr/><br/>'.join([get_task_cmd(task, sample, tid) for tid, task in enumerate(tasks)])

    return ''.join(['<p>', iframe_cmd, head_cmd, tasks_cmd, '</p>'])


def load_data(filename):
    _id = 0
    data = json.load(codecs.open(filename, 'r', encoding='utf-8'))
    for _, sample in data['data'].items():
        for annot_id in range(sample['annots_cnt']):
            cmd = get_cmd(sample, annot_id)
            _id = _id + 1
            outfile = f'_example/task-{_id:03d}.html'
            fileini = f'''---
title: "Visual-Linguistic Commonsense Reasoning Sample {_id:02d}"
collection: example
---

'''
            write_file(fileini + cmd, outfile)


if __name__ == '__main__':
    filename = 'files/toy.json'
    load_data(filename)