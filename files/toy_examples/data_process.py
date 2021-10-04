'''
CC coordinating conjunction
CD cardinal digit
DT determiner
EX existential there (like: “there is” … think of it like “there exists”)
FW foreign word
* IN preposition/subordinating conjunction
JJ adjective ‘big’
JJR adjective, comparative ‘bigger’
JJS adjective, superlative ‘biggest’
LS list marker 1)
# MD modal could, will
$ NN noun, singular ‘desk’
$ NNS noun plural ‘desks’
$ NNP proper noun, singular ‘Harrison’
$ NNPS proper noun, plural ‘Americans’
PDT predeterminer ‘all the kids’
POS possessive ending parent’s
$ PRP personal pronoun I, he, she
$ PRP$ possessive pronoun my, his, hers
RB adverb very, silently,
RBR adverb, comparative better
RBS adverb, superlative best
RP particle give up
TO, to go ‘to’ the store.
UH interjection, errrrrrrrm
# VB verb, base form take
# VBD verb, past tense took
# VBG verb, gerund/present participle taking
# VBN verb, past participle taken
# VBP verb, sing. present, non-3d take
# VBZ verb, 3rd person sing. present takes
WDT wh-determiner which
WP wh-pronoun who, what
WP$ possessive wh-pronoun whose
* WRB wh-abverb where, when
'''

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


def srl_portion(e1, e2):

    def cat_srl(e):
        srl = {'A':[], 'V':[], 'M':[]}
        for k, v in e.items():
            if k in ['Verb']:
                srl['V'].append(v['text'])
            elif k in ['Arg0', 'Arg1', 'Arg2']:
                srl['A'].append(v['text'])
            elif k in ['ArgM', 'Arg3', 'Arg4', 'Scene of the Event']:
                srl['M'].append(v['text'])
        return srl

    srl1, srl2 = cat_srl(e1), cat_srl(e2)
    x, y = 0, 0
    for k, v in srl1.items():
        for t in v:
            if t in srl2[k]:
                x += 1
            y += 1
    
    return x/y < 1/2 or (x/y < 1 and x < 3)


def get_abductive(events):
    verb_list = ['might have', 'may have', 'has possibly']
    time_list = ['before', 'in the interval', 'ealier']

    def get_qa_pair(evh, ev3):
        evh_args = [v['text'] for _,v in evh.items()]
        args = [(k, v['text']) for k,v in ev3.items() if k in ['Arg0', 'Arg1', 'Arg2'] and v['text'] in evh_args]
        
        random_verb = random.choice(verb_list)
        random_time = random.choice(time_list)

        q = f'what {random_verb} happened {random_time} ?'
        _id = 'basic'
        if len(args) > 0:
            key, arg = args[0]

            tags = [t[1] for t in pos_tag(arg.split())]
            if key in ['Arg0', 'Arg1']:
                if tags[0] not in ['DT', 'IN', 'PDT', 'PRP', 'PRP$', 'TO', 'WDT', 'WP', 'WP$', 'WRB']:
                    arg = ' '.join(['the', arg])
            elif key in ['Arg2']:
                if tags[0] not in ['IN', 'TO'] and not arg.split()[0].endswith('wards'):
                    arg = ' '.join(['towards', arg])

            if key == 'Arg0':
                random_verb = random_verb.split()
                span = ' '.join([random_verb[0], arg, random_verb[1]])
                q = f'what {span} done or been doing {random_time} ?'
                _id = key + ' ' + arg
            else:
                q = f'what {random_verb} happened to {arg} {random_time} ?'
                _id = 'others ' + arg
        return {'question': q, 'answer': srl_to_text(ev3), 'id': _id}

    def abductive_sample(e):
        frms = events['Ev1']['Frames'] + events['Ev2']['Frames']
        o1 = [frms[i*2 + 1] for i in range(4)]
        o2 = srl_to_text(events[e]['SRL'])
        
        qas = [get_qa_pair(events[e]['SRL'], events['Ev3']['SRL'])]
        for k in range(4, int(e[-1])):
            evk = events[f'Ev{k}']
            if srl_portion(evk['SRL'], events[e]['SRL']):
                qas += [get_qa_pair(evk['SRL'], events['Ev3']['SRL'])]
        hyp = {}
        for qa in qas:
            if qa['id'] in hyp:
                hyp[qa['id']].append(qa)
            else:
                hyp[qa['id']] = [qa]
        hyp = [{'question': v[0]['question'], 'answers': [vv['answer'] for vv in v]} for _,v in hyp.items()]

        return [{
            'label': 'abductive',
            'premise': o1, 'hypothese': o2,
            'question': h['question'], 'answers': h['answers']
        } for h in hyp]

    pairs, ev3, evhs = [], events['Ev3'], []
    for e in ['Ev4', 'Ev5']:
        evh = events[e]
        if srl_portion(ev3['SRL'], evh['SRL']):
            evhs.append({'name': e, 'rel': int(evh['EvRel'] == 'NoRel')})
    if len(evhs) > 1:
        evhs.sort(key=lambda x: (x['rel'], -int(x['name'][-1])), reverse=False)
    if len(evhs) > 0:
        pairs = abductive_sample(evhs[0]['name'])

    return pairs


def get_prediction(events):
    verb_list = ['is likely to', 'would', 'will', 'might', 'may', 'is gonna', 'is going to', 'is about to']
    time_list = ['next', 'after that', 'right after that', 'immediately after that', 'then', 'later']

    def get_qa_pair(evp, ev3):
        ev3_args = [v['text'] for _,v in ev3.items()]
        args = [(k, v['text']) for k,v in evp.items() if k in ['Arg0', 'Arg1', 'Arg2'] and v['text'] in ev3_args]
        
        random_verb = random.choice(verb_list)
        random_time = random.choice(time_list)
        
        q = f'what {random_verb} happen {random_time} ?'
        _id = 'basic'
        if len(args) > 0:
            key, arg = args[0]

            tags = [t[1] for t in pos_tag(arg.split())]
            if tags[0] in ['IN', 'TO'] or arg.split()[0].endswith('wards'):
                arg = ' '.join(arg.split()[1:])
                tags = tags[1:]
            if tags[0] not in ['PDT', 'PRP', 'PRP$', 'TO', 'WDT', 'WP', 'WP$', 'WRB']:
                arg = ' '.join(['the', arg])

            if key == 'Arg0':
                if random_verb.startswith('is'):
                    random_verb = random_verb.lstrip('is').strip()
                    q = f'what is {arg} {random_verb} do {random_time} ?'
                    _id = key + ' ' + arg
                else:
                    q = f'what {random_verb} {arg} do {random_time} ?'
                    _id = 'others ' + arg
            else:
                q = f'what {random_verb} happen to {arg} {random_time} ?'
        return {'question': q, 'answer': srl_to_text(evp), 'id': _id}

    def prediction_sample(evps):
        frm1, frm2 = events['Ev1']['Frames'], events['Ev2']['Frames']
        bg = [frm1[1], frm1[3], frm2[1], frm2[3]]
        hyp = srl_to_text(events['Ev3']['SRL'])

        qa_list = [get_qa_pair(events[evp]['SRL'], events['Ev3']['SRL']) for evp in evps]
        prd = {}
        for qa in qa_list:
            if qa['id'] in prd:
                prd[qa['id']].append(qa)
            else:
                prd[qa['id']] = [qa]
        prd = [{'question': v[0]['question'], 'answers': [vv['answer'] for vv in v]} for _, v in prd.items()]

        return[{
            'label': 'prediction',
            'premise': bg, 'hypothese': hyp,
            'question': p['question'], 'answers': p['answers']
        } for p in prd]

    pairs, ev3, evps, evbs = [], events['Ev3'], [], []
    for e in ['Ev4', 'Ev5']:
        evp = events[e]
        if evp['EvRel'] != 'NoRel' and srl_portion(evp['SRL'], ev3['SRL']):
            evps += [e]
    if len(evps) > 0:
        pairs = prediction_sample(evps)
    
    return pairs


def process_data(data):
    keys_to_remain = ['vid_seg_int', 'movie_name', 'genres', 'clip_name', 'text']
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
    data = [process_data(d) for d in tqdm(raw_data)]
    dump_data([d for d in data if d['task']['count'] > 0], sys.argv[2])
