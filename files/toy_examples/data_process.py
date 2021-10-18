import sys
import jsonlines
from tqdm import tqdm
import random
import string

from nltk import pos_tag 
from pycocoevalcap.bleu.bleu import Bleu
from pycocoevalcap.meteor.meteor import Meteor
from pycocoevalcap.rouge.rouge import Rouge
scorers = {
    "Bleu": Bleu(4),
    "Meteor": Meteor(),
    "Rouge": Rouge()
}


def load_data(filename):
    with jsonlines.open(filename) as reader:
        data = [sample for sample in reader]
    return data


def dump_data(data, filename):
    with jsonlines.open(filename, mode='w') as writer:
        assert isinstance(data, list)
        writer.write_all(data)


def get_abductive_task(vevs, levs, hev, rel_dict):
    verb_list_p = ['might have', 'may have', 'has possibly']
    time_list_p = ['before', 'in the interval', 'ealier', 'previously']
    verb_list_f = ['is likely to', 'would', 'will', 'might', 'may', 'is gonna', 'is going to', 'is about to']
    time_list_f = ['next', 'afterwards', 'right after the hypothetical event', 'immediately after the hypothetical event', 'then', 'later']
    random_verb_p = random.choice(verb_list_p)
    random_time_p = random.choice(time_list_p)
    random_verb_f = random.choice(verb_list_f)
    random_time_f = random.choice(time_list_f)

    def _bleu_score(gt, hyp):
        score, _ = scorers['Bleu'].compute_score({1:[gt]}, {1:[hyp]}, verbose=0)
        return score
    
    def _process(text):
        tokens = text.split()
        tags = [t[1] for t in pos_tag(tokens)]
        while len(tags) > 0 and (tags[0] in ['IN', 'TO'] or tokens[0].endswith('wards') or tokens[0].endswith('ward')):
            tokens, tags = tokens[1:], tags[1:]
        if len(tags) == 0:
            return ''
        if tags[0] not in ['DT', 'PDT', 'PRP', 'PRP$', 'WDT', 'WP', 'WP$', 'WRB', 'NNPS', 'NNS']:
            if tokens[0] not in ['something', 'nothing', 'anything', 'everything', 'someone', 'noone', 'anyone', 'everyone']:
                tokens, tags = ['the'] + tokens, ['DT'] + tags
        return ' '.join(tokens).lower()

    def _get_args(ev):
        rst = {
            k: _process(v['text'].strip()) for k,v in ev['SRL'].items() \
            if k in ['Arg0', 'Arg1', 'Arg2']
        }
        return {k:v for k,v in rst.items() if v}

    def _get_question(target, predict=False):
        if predict:
            random_verb, random_time = random_verb_f, random_time_f
        else:
            random_verb, random_time = random_verb_p, random_time_p
        values = list(target.values())
        target = {k:target[k] for i, k in enumerate(target) if target[k] not in values[:i]}
        
        q = f'What {random_verb} happened {random_time}?'
        if len(target) > 1:
            arg0, arg1 = list(target.values())[:2]
            q = f'What {random_verb} happened to {arg0} and {arg1} {random_time}?'
        elif len(target) > 0:
            arg0 = list(target.values())[0]
            q = f'What {random_verb} happened to {arg0} {random_time}?'
        
        return q

    video_time = [vevs[0]['eid'] * 2 - 2, vevs[-1]['eid'] * 2]

    reference = [x for ev in vevs + [levs[-1]] for x in list(_get_args(ev).values())]
    target = {k:v for k,v in _get_args(hev).items() if v in reference}
    question = _get_question(target)
    
    tasks = [{
        'type': 'abductive',
        'premise_v': video_time,
        'result_l': levs[-1]['TXT'],
        'hypothesis': [hev['TXT']],
        'question': question
    }]
    if len(vevs) > 1 and vevs[-1]['EvRel'] != 'NoRel' and 'TXT' in vevs[-1]:
        if _bleu_score(hev['TXT'] + ' ' + levs[-1]['TXT'], vevs[-1]['TXT'])[1] < 0.6:
            reference = [x for ev in vevs[:-1] + [hev] + levs for x in list(_get_args(ev).values())]
            target = {k:v for k,v in _get_args(vevs[-1]).items() if v in reference}
            tasks += [{
                'type': 'abductive_v',
                'premise_v': [vevs[0]['eid'] * 2 - 2, vevs[0]['eid'] * 2],
                'result_l': hev['TXT'] + ' ' + levs[-1]['TXT'],
                'hypothesis': [vevs[-1]['TXT']],
                'question': _get_question(target)
            }]
    pre_tasks = {}
    for evt in levs:
        if evt['EvRel'] != 'NoRel' and _bleu_score(hev['TXT'], evt['TXT'])[1] < 0.6:
            reference = [x for ev in vevs + [hev] for x in list(_get_args(ev).values())]
            target = {k:v for k,v in _get_args(evt).items() if v in reference}
            key = '; '.join(list(target.values())) if len(target) > 0 else 'none'
            if key in pre_tasks:
                pre_tasks[key].append((evt['TXT'], target))
            else:
                pre_tasks[key] = [(evt['TXT'], target)]
    if len(pre_tasks) > 0 and 'none' in pre_tasks:
        del pre_tasks['none']
    
    key_list = list(pre_tasks.keys())
    for key in pre_tasks:
        candidates = [key != k and pre_tasks[k] is not None and all(ky in key for ky in k.split('; ')) for k in pre_tasks]
        if any(candidates):
            try:
                pre_tasks[key_list[candidates.index(True)]] += pre_tasks[key]
            except:
                import ipdb; ipdb.set_trace()
            pre_tasks[key] = None
    
    if len(pre_tasks) > 1:
        import ipdb; ipdb.set_trace()

    for k, v in pre_tasks.items():
        if not isinstance(v, list): continue
        v.sort(key=lambda x: len(x[1]), reverse=False)
        target = v[0][1]
        tasks += [{
            'type': 'predictive',
            'premise_v': video_time,
            'premise_l': hev['TXT'],
            'hypothesis': [x[0] for x in v],
            'question': _get_question(target, predict=True)
        }]
    
    return tasks


def overlap(vevs, levs, hev):

    def _bleu_score(gt, hyp):
        score, _ = scorers['Bleu'].compute_score({1:[gt]}, {1:[hyp]}, verbose=0)
        return score

    if 'TXT' not in hev:
        return {'flag': False}
    
    vrst, lrst, flag = 0, 0, 0
    for i, ev in enumerate(levs):
        if 'TXT' in ev:
            scores = _bleu_score(ev['TXT'], hev['TXT'])
            if scores[1] < 0.6:
                lrst += i + 1
                if scores[0] > 0.08:
                    flag = 1
    for i, ev in enumerate(vevs):
        ev_txt = ' '.join([v['text'] for _,v in ev['SRL'].items()]).lower()
        hev_txt = ' '.join([v['text'] for _,v in hev['SRL'].items()]).lower()
        scores = _bleu_score(ev_txt, hev_txt)
        if scores[1] < 0.8:
            vrst += i + 1
            if scores[0] > 0.08:
                flag = 1

    return {'flag': vrst * lrst * flag > 0, 'v': vrst, 'l': lrst}


def get_relations(Ev):
    before = {'Causes': 'causes', 'Enables': 'enables', 'Reaction To': 'motivates', 'NoRel': ''}
    after = {'Causes': 'is caused by', 'Enables': 'is enabled by', 'Reaction To': 'is reaction to', 'NoRel': ''}
    
    rel_dict = {i: {j: '' for j in range(1, 6) if j != i} for i in range(1, 6)}
    for i in range(1, 6):
        if i < 3:
            rel_dict[i][3] = before[Ev[f'Ev{i}']['EvRel']]
            rel_dict[3][i] = after[Ev[f'Ev{i}']['EvRel']]
        elif i > 3:
            rel_dict[i][3] = after[Ev[f'Ev{i}']['EvRel']]
            rel_dict[3][i] = before[Ev[f'Ev{i}']['EvRel']]
    
    for i in range(1, 3):
        for j in range(4, 6):
            if rel_dict[i][3] and rel_dict[j][3]:
                rel_dict[i][j] = ' '.join([rel_dict[i][3], 'Ev3', rel_dict[3][j]])
                rel_dict[j][i] = ' '.join([rel_dict[j][3], 'Ev3', rel_dict[3][i]])
    
    return rel_dict


def translate_to_text(e, _id):
    e['eid'] = _id
    ev = e['SRL']
    to_remain = [k for k in ev if k in ['Arg0', 'Arg1', 'Arg2', 'Verb']]
    # keys = ['Arg0', 'Verb', 'Arg1', 'Arg2', 'Arg3', 'Arg4', 'ArgM', 'Scene of the Event']
    spans = {}
    for k, v in ev.items():
        v['desc'] = '' if v['desc'] is None else v['desc'].lower()
        text = v['text'].strip()
        if any(c not in string.punctuation for c in text) and len(text) > 0:
            ## get the POS tags
            tokens = text.split()
            tags = [t[1] for t in pos_tag(tokens)]
            ## refine the text according to its type
            if k in ['Arg0', 'Arg1', 'Arg2']:
                # add DT to nouns
                if tags[0] not in ['DT', 'IN', 'PDT', 'PRP', 'PRP$', 'TO', 'WDT', 'WP', 'WP$', 'WRB', 'NNPS', 'NNS']:
                    if tokens[0] not in ['something', 'nothing', 'anything', 'everything', 'someone', 'noone', 'anyone', 'everyone']:
                        if not tokens[0].endswith('wards') and not tokens[0].endswith('ward'):
                            tokens, tags = ['the'] + tokens, ['DT'] + tags
                            if 'Arg0' in spans and ' '.join(tokens).lower() == spans['Arg0']:
                                tokens, tags = ['themselves'], ['NNS']
            if k in ['Arg2'] or any(x in v['desc'] for x in ['instrument', 'benefactive', 'attribute']):
                # add towards/to/for to Arg2 phrases
                if tags[0] not in ['IN', 'TO'] and not tokens[0].endswith('wards') and not tokens[0].endswith('ward'):
                    if tags[0] in ['VB', 'VBP']:
                        tokens, tags = ['to'] + tokens, ['TO'] + tags
                    else:
                        tokens, tags = ['towards'] + tokens, ['IN'] + tags
            elif k == 'Arg3' and 'start' in v['desc'] and tokens[0] != 'from':
                # start point
                tokens, tags = ['from'] + tokens, ['IN'] + tags
            elif (k == 'Arg4' or 'destination' in v['desc']) and not tokens[0].endswith('to'):
                # end point
                tokens, tags = ['to'] + tokens, ['TO'] + tags
            elif k == 'Scene of the Event' or 'location' in v['desc']:
                # location / scene / place
                if tags[0] not in ['IN', 'TO', 'WRB']:
                    if tags[0] not in ['DT', 'PDT', 'WDT'] and not tokens[0].endswith('where'):
                        tokens, tags = ['the'] + tokens, ['DT'] + tags
                    tokens, tags = ['in'] + tokens, ['IN'] + tags
            elif k == 'ArgM':
                # goal / purpose
                if 'goal' in v['desc'] or 'purpose' in v['desc']:
                    if tags[0] not in ['TO', 'IN']:
                        tokens, tags = ['to'] + tokens, ['TO'] + tags
            
            text = ' '.join(tokens).lower()
            spans[k] = text
    
    if all(x in spans for x in to_remain):
        e['TXT'] = ' '.join(list(spans.values()))  + '.'
        e['TXT'] = e['TXT'][0].upper() + e['TXT'][1:]

    return e


def get_task(events):
    rel_dict = get_relations(events)
    ev = {int(k[-1]): translate_to_text(e, int(k[-1])) for k, e in events.items()}
    tasks = []
    
    if rel_dict[3][5] or rel_dict[3][4]:
        ovlp = overlap([ev[1], ev[2]], [ev[4], ev[5]], ev[3])
        vev, lev = [], []
        if ovlp['flag']:
            if ovlp['v'] in [1, 3]:
                vev.append(ev[1])
            if ovlp['v'] >= 2:
                vev.append(ev[2])
            if ovlp['l'] in [1, 3]:
                lev.append(ev[4])
            if ovlp['l'] >= 2:
                lev.append(ev[5])
            tasks += get_abductive_task(vev, lev, ev[3], rel_dict)
    elif rel_dict[2][3]:
        ovlp = overlap([ev[1]], [ev[3]], ev[2])
        if ovlp['flag']:
            tasks += get_abductive_task([ev[1]], [ev[3]], ev[2], rel_dict)
    
    # if len(tasks) == 0:
    #     import ipdb; ipdb.set_trace()
    
    return tasks


def process_data_task(data):
    keys_to_remain = ['vid_seg_int', 'movie_name', 'genres', 'clip_name', 'text', 'events', 'desc']
    sample = {k:data[k] for k in keys_to_remain}

    tasks = get_task(data['events'])
    sample['task'] = {
        'count': len(tasks),
        'tasks': tasks
    }

    return sample


if __name__ == '__main__':
    raw_data = load_data(sys.argv[1])
    data = [process_data_task(d) for d in tqdm(raw_data)]
    dump_data([d for d in data if d['task']['count'] > 0], sys.argv[2])
