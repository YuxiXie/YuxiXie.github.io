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


def get_task_cmd_abd(task, vid, tid):
    label_cmd = f'<strong><font size="4"> task {tid} </font></strong>' \
        + '<li><strong>[task type]</strong> <font color=DarkRed>ABDUCTIVE</font> </li>'

    end = task['observation']['end state']
    frames = ['https://yuxixie.github.io/files/toy_examples/video_frames_dir/' + vid + '.' + frm + '.jpg' for frm in task['observation']['background']]
    frames = ''.join([f'<td><img src="{frm}" width="360" height="240"></td>' for frm in frames])
    obv_cmd = '<li><strong>[observations]</strong><br/> <font color=YellowGreen>[1] <code>(background)</code></font> ' \
        + f'<table>{frames}</table> <font color=DodgerBlue>[2] <code>(end state)</code></font><br/> {end} </li>'
    
    hyp = '<br/>'.join(['({x}) {h}'.format(x=i+1, h=h) for i, h in enumerate(task['hypotheses'])])
    hyp_cmd = f'<li><strong><font color=BlueViolet>[hypotheses]</font></strong><br/> {hyp} </li>'

    cmd = label_cmd + obv_cmd + hyp_cmd
    return cmd


def get_task_cmd_prd(task, vid, tid):
    label_cmd = f'<strong><font size="4"> task {tid} </font></strong>' \
        + '<li><strong>[task type]</strong> <font color=DarkGreen>PREDICTION</font> </li>'

    frames = ['https://yuxixie.github.io/files/toy_examples/video_frames_dir/' + vid + '.' + frm + '.jpg' for frm in task['premise']]
    frames = ''.join([f'<td><img src="{frm}" width="360" height="240"></td>' for frm in frames])
    bg_cmd = '<li><strong><font color=YellowGreen>[premise]</font></strong> <code>(background)</code> <br/>' \
        + f'<table>{frames}</table> </li>'
    
    hyp = task['hypothese']
    hyp_cmd = f'<li><strong><font color=DodgerBlue>[hypothese]</font></strong> <code>(activation)</code> {hyp} </li>'

    prd = '<br/>'.join(['({x}) {p}'.format(x=i+1, p=p) for i, p in enumerate(task['prediction'])])
    prd_cmd = f'<li><strong><font color=BlueViolet>[prediction]</font></strong><br/> {prd} </li>'

    cmd = label_cmd + bg_cmd + hyp_cmd + prd_cmd
    return cmd


def get_task_cmd(task, vid, tid):
    tid = tid + 1

    label = task['type'].upper()
    label_color = 'DarkGreen' if task['type'] == 'abductive' else 'DarkRed'
    label_cmd = f'<strong><font size="4"> task {tid} </font></strong>' \
        + f'<li><strong>[task type]</strong> <font color={label_color}>{label}</font> </li>'
    
    # frames = ['https://yuxixie.github.io/files/heval_examples/video_frames_dir/' + vid + '.' + frm + '.jpg' for frm in task['premise']]
    # frames_cmd = ''.join([f'<td><img src="{frm}" width="360" height="240"></td>' for frm in frames[:4]])
    # if len(frames) <= 4:
    #     frames_cmd = '<tr>' + frames_cmd + '<td></td>' * (4 - len(frames)) + '</tr>'
    # else:
    #     frames_cmd = '<tr>' + frames_cmd + '</tr><tr>' \
    #         + ''.join([f'<td><img src="{frm}" width="360" height="240"></td>' for frm in frames[4:]]) \
    #         + '<td></td>' * (8 - len(frames)) + '</tr>'

    # pm_cmd = '<li><strong><font color=YellowGreen>[premise]</font></strong> <code>(observation 1)</code> <br/>' \
    #     + f'<table>{frames_cmd}</table> </li>'
    
    add_pre = ''
    if 'premise_l' in task:
        prm = task['premise_l']
        add_pre = f'<li><strong><font color=DodgerBlue>[premise]</font></strong> <code>(observed premise)</code> {prm} </li>'
    
    hyp = task['result_l']
    hyp_cmd = f'<li><strong><font color=DodgerBlue>[hypothesis]</font></strong> <code>(observed result)</code> {hyp} </li>'

    qu = task['question']
    # all_answers = {}
    # for ans in task['answers']:
    #     if ans['ans'] not in all_answers:
    #         all_answers[ans['ans']] = ans
    # all_answers = list(all_answers.values())
    # ans = ''.join([
    #     '<tr><td bgcolor=LemonChiffon><strong><font size="4">A{x}</font></strong></td>'.format(x=i+1) \
    #     + '<td bgcolor=LemonChiffon><code>{r}</code><font size="4"> {a}</font></td></tr>'.format(r=a['rel'], a=a['ans']) \
    #     for i, a in enumerate(all_answers)
    # ])
    a = task['hypothesis']
    ans = '<tr><td bgcolor=LemonChiffon><strong><font size="4">A</font></strong></td>' \
        + f'<td bgcolor=LemonChiffon><font size="4">{a}</font></td></tr>'
    qu_ans = f'<table><tr><td width="30" bgcolor=LightPink><strong><font size="4">Q</font></strong></td><td bgcolor=LightPink><font size="4">{qu}</font></td></tr>{ans}</table>'
    qa_cmd = f'<li><strong><font color=BlueViolet>[question-answers]</font></strong><br/> {qu_ans} </li>'

    return ' '.join(['<tr>', label_cmd, add_pre, hyp_cmd, qa_cmd, '</tr>'])


def get_frames_premise(frames, vid):
    frames = ['https://yuxixie.github.io/files/heval_examples/video_frames_dir/' + vid + '.' + frm + '.jpg' for frm in frames]
    frames_cmd = ''.join([f'<td><img src="{frm}" width="360" height="240"></td>' for frm in frames[:4]])
    if len(frames) <= 4:
        frames_cmd = '<tr>' + frames_cmd + '<td></td>' * (4 - len(frames)) + '</tr>'
    else:
        frames_cmd = '<tr>' + frames_cmd + '</tr><tr>' \
            + ''.join([f'<td><img src="{frm}" width="360" height="240"></td>' for frm in frames[4:]]) \
            + '<td></td>' * (8 - len(frames)) + '</tr>'
    pm_cmd = f'<table>{frames_cmd}</table>'
    return pm_cmd


def get_cmd(sample):
    vid_seg_int = sample['vid_seg_int'].split('_')
    vid = '_'.join(vid_seg_int[1:-3])

    movie, clip, desc, bgdesc = sample['movie_name'], sample['clip_name'], sample['text'], sample['desc']
    genres = [] if sample['genres'] == 'NA' else json.loads(sample['genres'].replace("'", '"'))
    genres = ''.join([f'<code>{gen}</code>' for gen in genres])
    head_cmd = f'<strong><font color=DodgerBlue>[Movie]</font> {movie}  <font color=DodgerBlue>[Clip]</font> {clip} </strong> {genres}<br/>' \
        + f'<strong><font color=DodgerBlue>[Desc]</font></strong> {desc}<br/>'

    start, end = vid_seg_int[-2], int(vid_seg_int[-2]) + 4
    iframe_cmd = f'<strong><font color=DodgerBlue>[Background]</font></strong> {bgdesc}<br/>' \
        + f'<strong><font color=YellowGreen>[Premise]</font></strong> You can also refer to the thumbnail (for replaying: please refresh the page). <br/>' \
        + f'<iframe src="https://www.youtube.com/embed/{vid}?start={start}&end={end}&version=3" ' \
        + f'scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width="900" height="600"></iframe> <br/>' 
        # + get_frames_premise(sample['task']['tasks'][0]['premise'], sample['vid_seg_int'])
    
    task_cnt = sample['task']['count']
    task_brief = f'<strong><font color=BlueViolet>[Tasks]</font></strong> {task_cnt} reasoning task(s) in total <br/><br/>'
    tasks_cmd = task_brief + '<br/><hr/><br/>'.join([get_task_cmd(task, sample['vid_seg_int'], tid) for tid, task in enumerate(sample['task']['tasks'])])

    return ''.join(['<p>', iframe_cmd, head_cmd, tasks_cmd, '</p>'])


def load_data(filename):
    cmd_list = []
    with jsonlines.open(filename) as reader:
        for idx, sample in enumerate(reader):
            cmd = get_cmd(sample)
            _id = idx + 1
            vid = sample['vid_seg_int']
            outfile = f'_example/task-{_id:02d}.html'
            fileini = f'''---
title: "Visual-Linguistic Commonsense Reasoning Sample {_id:02d}"
collection: example
---

'''
            write_file(fileini + cmd, outfile)

if __name__ == '__main__':
    filename = 'files/heval_examples/heval-only.jsonl'
    load_data(filename)