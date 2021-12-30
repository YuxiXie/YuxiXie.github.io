import json
import codecs
import jsonlines

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

    pm_cmd = f'<li><strong><font color=YellowGreen>[Premise]</font></strong> <code>{vid_in}</code> <br/>'

    rst = ' '.join([sample[f'ev{x}']['desc'] for x in txt_in])
    rst_cmd = f'<li><strong><font color=DodgerBlue>[Observation]</font></strong> {rst} </li>'
    
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
    qa_cmd = f'<li><strong><font color=BlueViolet>[Hypothesis]</font></strong><br/> {qu_ans} </li>'

    return ' '.join(['<tr>', label_cmd, pm_cmd, rst_cmd, qa_cmd, '</tr>'])


def get_cmd(annots):
    vid_seg_int = annots[0]['vid'].split('_')
    vid = '_'.join(vid_seg_int[1:-3])

    movie, clip, desc = annots[0]['movie'], annots[0]['clip'], annots[0]['desc']
    genres = annots[0]['genres'] if isinstance(annots[0]['genres'], list) else []
    genres = ''.join([f'<code>{gen}</code>' for gen in genres])
    head_cmd = f'<strong><font color=DodgerBlue>[Movie]</font> {movie}  <font color=DodgerBlue>[Clip]</font> {clip} </strong> {genres}<br/>' \
        + f'<strong><font color=DodgerBlue>[Desc]</font></strong> {desc}<br/>' \
        + '<strong>{} task(s) in total </strong><br/><br/>'.format(len(annots))

    task_cmd = []
    for sample in annots:
        is_vis_premise = isinstance(sample['premise'], list)
    
        timestamps = sample['premise'] if is_vis_premise else sample['observation']
        start = int(vid_seg_int[-2]) + (timestamps[0] - 1) * 2
        end = int(vid_seg_int[-2]) + timestamps[1] * 2
        _type = 'Premise' if is_vis_premise else 'Observation'
        iframe_cmd = f'<li><strong><font color=YellowGreen>[{_type}]</font></strong> You can also refer to the thumbnail (for replaying: please refresh the page). <br/>' \
            + f'<iframe src="https://www.youtube.com/embed/{vid}?start={start}&end={end}&version=3" ' \
            + 'scrolling="yes" frameborder="yes" framespacing="0" allowfullscreen="true" width="450" height="300"></iframe></li>'
        
        nar = sample['observation'] if is_vis_premise else sample['premise']
        _type = 'Observation' if is_vis_premise else 'Premise'
        nar_cmd = f'<li><strong><font color=DodgerBlue>[{_type}]</font></strong> {nar} </li>'
        
        prm_cmd = iframe_cmd if is_vis_premise else nar_cmd
        obs_cmd = nar_cmd if is_vis_premise else iframe_cmd
        
        ans = ''.join([
            f'<tr><td bgcolor=LemonChiffon><strong><font size="4">A{i}</font></strong></td>' \
            + f'<td bgcolor=LemonChiffon><font size="4">{a}</font></td></tr>' for i, a in enumerate(sample['hypothesis'], 1)
        ])    
        qu_ans = '<table><tr><td bgcolor=LightBlue><strong><font size="4">Q</font></strong></td>' \
            + '<td bgcolor=LightBlue><font size="4">{}</font></td></tr>'.format(sample['question']) \
            + f'{ans}</table>'
        qa_cmd = f'<li><strong><font color=BlueViolet>[Hypothesis]</font></strong><br/> {qu_ans} </li>'

        task_cmd.append(' '.join(['<tr>', prm_cmd, obs_cmd, qa_cmd, '</tr>']))
    task_cmd = ' <br/> '.join(task_cmd)

    return ''.join([head_cmd, task_cmd])


def load_comet(filename):
    data = {}
    with jsonlines.open(filename, mode='r') as reader:
        for line in reader:
            data[line['id']] = line
    return data


def load_data(filename, cometname=None):
    idx = 0
    data = json.load(codecs.open(filename, 'r', encoding='utf-8'))
    samples = {}
    comet = load_comet(cometname) if cometname else None
    for sample in data['data']:
        if not sample['to_train']: continue
        _id = sample['vid'] + '_' + str(sample['annot_id'])
        if _id not in samples:
            samples[_id] = []
        samples[_id].append(sample)
    for _, sample in samples.items():
        cmd = '<p> ' + get_cmd(sample)
        if comet is not None:
            for sp in sample:
                if sp['id'] in comet and comet[sp['id']]['vid'] == sample[0]['vid']:
                    rsts = comet[sp['id']]['rst']
                    rst = rsts[0]
                    ccmd = ' <br/>  <br/> ' + ' <br/> '.join([
                        '[{}] {}'.format('P', rst['q']), '[{}] {}'.format('HC', rst['p']), '[{}] {}'.format('HO', rst['h'])])
                    rst = rsts[1]
                    ccmd += ' <br/> ' + ' <br/> '.join([
                        '[{}] {}'.format('P', rst['q']), '[{}] {}'.format('HC', rst['p']), '[{}] {}'.format('HO', rst['h'])])
                    cmd += ccmd
        cmd += ' </p>'
        idx = idx + 1
        outfile = f'_example/task-{idx:03d}.html'
        fileini = f'''---
title: "Visual-Linguistic Commonsense Reasoning Sample {idx:03d}"
collection: example
---

'''
        write_file(fileini + cmd, outfile)


if __name__ == '__main__':
    filename = 'files/roberta-large_filled_toy.json'
    cometname = 'files/comet.json'
    load_data(filename, cometname=cometname)