import sys
import jsonlines
from tqdm import tqdm
import random

from nltk import pos_tag 


def load_data(filename):
    with jsonlines.open(filename) as reader:
        data = [sample for sample in reader]
    return data


def dump_data(data, filename):
    with jsonlines.open(filename, mode='w') as writer:
        assert isinstance(data, list)
        writer.write_all(data)


def srl_to_text(srl):
    # keys = ['Arg0', 'Verb', 'Arg1', 'Arg2', 'Arg3', 'Arg4', 'ArgM', 'Scene of the Event']
    spans = []
    for k, v in srl.items():
        text = v['text'].strip()
        if text not in ['...', '']:
            tokens = text.split()
            tags = [t[1] for t in pos_tag(tokens)]
            
            if k in ['Arg0', 'Arg1']:
                if tags[0] not in ['DT', 'IN', 'PDT', 'PRP', 'PRP$', 'TO', 'WDT', 'WP', 'WP$', 'WRB']:
                    text = ' '.join(['the', text])
            elif k in ['Arg2']:
                if tags[0] not in ['IN', 'TO'] and not tokens[0].endswith('wards'):
                    text = ' '.join(['towards', text])
            elif k == 'Arg3':
                text = ' '.join(['from', text]) if tokens[0] != 'from' else text
            elif k == 'Arg4':
                text = ' '.join(['to', text]) if tokens[0] != 'to' else text
            elif k == 'Scene of the Event':
                if tags[0] not in ['IN', 'TO', 'WRB']:
                    if tags[0] not in ['DT', 'PDT', 'WDT']:
                        text = ' '.join(['the', text])
                    text = ' '.join(['in', text])
            elif k == 'ArgM':
                if 'goal' in v['desc'] and tags[0] not in ['TO', 'IN']:
                    text = ' '.join(['to', text])
            
            text = text.lower() if text != 'I' else text
            spans.append(text)
    
    return ' '.join(spans)


def srl_portion(ep, eh, e1, e2):

    def cat_srl(e):
        pos = ['NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'VBD', 'VBN', 'VBG']
        srl = {'all': [], 'special': []}
        for k, v in e.items():
            text = v['text']
            if k not in ['Verb']:
                tags = pos_tag(text.split())
                while text and (tags[0][1] not in pos or tags[0][0].endswith('wards')):
                    text = ' '.join(text.split()[1:])
                    tags = tags[1:]
            if text:
                if k not in ['ArgM', 'Arg3', 'Arg4']:
                    srl['all'] += [text.lower()]
                if k not in ['Verb', 'Scene of the Event', 'ArgM', 'Arg3', 'Arg4']:
                    srl['special'] += [x for tag, x in zip(tags, text.lower().split()) if tag[1] in pos]
        return srl

    srl = cat_srl(ep)
    th = ' '.join([v['text'].lower() for _,v in eh.items()])
    t12 = ' '.join([v['text'].lower() for _,v in e1.items()]) + ' ' + ' '.join([v['text'].lower() for _,v in e2.items()]) 

    x, all_cnt = sum(int(t in th) for t in srl['all']), len(srl['all'])   # language bias
    y, spc_cnt = sum(int(t in t12 + ' ' + th) for t in srl['special']), len(srl['special']) # answerable

    # if srl_to_text(ep) == "the kid walk dejected in the house":
    #     import ipdb; ipdb.set_trace()
    
    return x / max(1, all_cnt) < 1 and (y / max(1, spc_cnt) > 1/2 or spc_cnt < 2)


def get_abductive(events):
    verb_list = ['might have', 'may have', 'has possibly']
    time_list = ['before', 'in the interval', 'ealier', 'previously']

    def get_qa_pair(evh, ev3, rel):
        evh_args = [v['text'] for _,v in evh.items()]
        args = [(k, v['text']) for k,v in ev3.items() if k in ['Arg0', 'Arg1', 'Arg2'] and v['text'] in evh_args]
        
        random_verb = random.choice(verb_list)
        random_time = random.choice(time_list)

        q = f'what {random_verb} happened {random_time} ?'
        _id = 'basic'
        for i in range(len(args)):
            key, arg = args[i]

            tags = [t[1] for t in pos_tag(arg.split())]
            if tags[0] in ['IN', 'TO'] or arg.split()[0].endswith('wards'):
                arg = ' '.join(arg.split()[1:])
                tags = tags[1:]
            if arg and tags[0] not in ['PDT', 'PRP', 'PRP$', 'TO', 'WDT', 'WP', 'WP$', 'WRB']:
                arg = ' '.join(['the', arg])            
            arg = arg.lower() if arg != 'I' else arg

            if arg:
                if key == 'Arg0':
                    random_verb = random_verb.split()
                    span = ' '.join([random_verb[0], arg, random_verb[1]])
                    q = f'what {span} done or been doing {random_time} ?'
                    _id = key + ' ' + arg
                else:
                    q = f'what {random_verb} happened to {arg} {random_time} ?'
                    _id = 'others ' + arg
                break
        
        return {'question': q, 'answer': srl_to_text(ev3), 'id': _id, 'rel': rel}

    def abductive_sample(e):
        frms = events['Ev1']['Frames'] + events['Ev2']['Frames']
        o1 = frms   # [frms[i*2 + 1] for i in range(4)]
        o2 = srl_to_text(events[e]['SRL'])
        
        rel_dict = {'Causes': 'cause', 'Enables': 'condition', 'Reaction To': 'trigger', 'NoRel': 'temporal'}
        rel = rel_dict[events[e]['EvRel']]
        qas = [get_qa_pair(events[e]['SRL'], events['Ev3']['SRL'], rel)]
        
        for k in range(4, int(e[-1])):
            evk = events[f'Ev{k}']
            if srl_portion(evk['SRL'], events[e]['SRL'], events['Ev1']['SRL'], events['Ev2']['SRL']):
                qas += [get_qa_pair(events[e]['SRL'], evk['SRL'], 'temporal')]
        
        hyp = {}
        for qa in qas:
            if qa['id'] in hyp:
                hyp[qa['id']].append(qa)
            else:
                hyp[qa['id']] = [qa]
        hyp = [
            {'question': v[0]['question'], 'answers': [{'ans': vv['answer'], 'rel': vv['rel']} for vv in v]
        } for _,v in hyp.items()]

        return [{
            'label': 'abductive',
            'premise': o1, 'hypothese': o2,
            'question': h['question'], 'answers': h['answers']
        } for h in hyp]

    pairs, ev3, evhs = [], events['Ev3'], []
    for e in ['Ev4', 'Ev5']:
        evh = events[e]
        if srl_portion(ev3['SRL'], evh['SRL'], events['Ev1']['SRL'], events['Ev2']['SRL']):
            evhs.append({'name': e, 'rel': int(evh['EvRel'] == 'NoRel')})
    if len(evhs) > 1:
        evhs.sort(key=lambda x: (x['rel'], -int(x['name'][-1])), reverse=False)
    if len(evhs) > 0:
        pairs = abductive_sample(evhs[0]['name'])

    return pairs


def get_prediction(events):
    verb_list = ['is likely to', 'would', 'will', 'might', 'may', 'is gonna', 'is going to', 'is about to']
    time_list = ['next', 'afterwards', 'right after the hypothetical event', 'immediately after the hypothetical event', 'then', 'later']

    def get_qa_pair(evp, ev3, rel):
        ev3_args = [v['text'] for _,v in ev3.items()]
        args = [(k, v['text']) for k,v in evp.items() if k in ['Arg0', 'Arg1', 'Arg2'] and v['text'] in ev3_args]
        
        random_verb = random.choice(verb_list)
        random_time = random.choice(time_list)
        
        q = f'what {random_verb} happen {random_time} ?'
        _id = 'basic'
        for i in range(len(args)):
            key, arg = args[i]

            tags = [t[1] for t in pos_tag(arg.split())]
            if tags[0] in ['IN', 'TO'] or arg.split()[0].endswith('wards'):
                arg = ' '.join(arg.split()[1:])
                tags = tags[1:]
            if arg and tags[0] not in ['PDT', 'PRP', 'PRP$', 'TO', 'WDT', 'WP', 'WP$', 'WRB']:
                arg = ' '.join(['the', arg])            
            arg = arg.lower() if arg != 'I' else arg

            if arg:
                if key == 'Arg0':
                    if random_verb.startswith('is'):
                        random_verb = random_verb.lstrip('is').strip()
                        q = f'what is {arg} {random_verb} do {random_time} ?'
                    else:
                        q = f'what {random_verb} {arg} do {random_time} ?'
                    _id = key + ' ' + arg
                else:
                    q = f'what {random_verb} happen to {arg} {random_time} ?'
                    _id = 'others ' + arg
                break
        
        return {'question': q, 'answer': srl_to_text(evp), 'id': _id, 'rel': rel}

    def prediction_sample(evps):
        frms = events['Ev1']['Frames'] + events['Ev2']['Frames']
        bg = frms   # [frms[i*2 + 1] for i in range(4)]
        hyp = srl_to_text(events['Ev3']['SRL'])

        qa_list = [get_qa_pair(events[evp[0]]['SRL'], events['Ev3']['SRL'], evp[1]) for evp in evps]
        prd = {}
        for qa in qa_list:
            if qa['id'] in prd:
                prd[qa['id']].append(qa)
            else:
                prd[qa['id']] = [qa]
        prd = [
            {'question': v[0]['question'], 'answers': [{'ans': vv['answer'], 'rel': vv['rel']} for vv in v]
        } for _, v in prd.items()]

        return[{
            'label': 'prediction',
            'premise': bg, 'hypothese': hyp,
            'question': p['question'], 'answers': p['answers']
        } for p in prd]

    pairs, ev3, evps, evbs = [], events['Ev3'], [], []
    for e in ['Ev4', 'Ev5']:
        evp = events[e]
        rel_dict = {'Causes': 'effect', 'Enables': 'temporal', 'Reaction To': 'reaction', 'NoRel': 'temporal'}
        if srl_portion(evp['SRL'], ev3['SRL'], events['Ev1']['SRL'], events['Ev2']['SRL']):
            evps += [(e, rel_dict[evp['EvRel']])]
    if len(evps) > 0:
        pairs = prediction_sample(evps)
    
    return pairs


def process_data(data):
    keys_to_remain = ['vid_seg_int', 'movie_name', 'genres', 'clip_name', 'text', 'desc']
    sample = {k:data[k] for k in keys_to_remain}

    events = data['events']
    abductives = get_abductive(events)
    predictions = get_prediction(events)
    sample['task'] = {
        'count': len(abductives) + len(predictions),
        'tasks': abductives + predictions
    }

    return sample


def process_data_task(data):
    keys_to_remain = ['vid_seg_int', 'movie_name', 'genres', 'clip_name', 'text', 'events', 'desc']
    sample = {k:data[k] for k in keys_to_remain}

    events = data['events']
    abductives = get_abductive(events)
    predictions = get_prediction(events)
    sample['task'] = {
        'count': len(abductives) + len(predictions),
        'tasks': abductives + predictions
    }

    return sample


if __name__ == '__main__':
    raw_data = load_data(sys.argv[1])
    data = [process_data_task(d) for d in tqdm(raw_data)]
    dump_data([d for d in data if d['task']['count'] > 0], sys.argv[2])
