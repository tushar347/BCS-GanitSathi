#!/usr/bin/env python3
"""Validate a single collection without third-party dependencies."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIXES=['algebra','percentages','ratios','speed_distance','arithmetic','mental_ability','geometry','mensuration','number_system']
Q_KEYS={'family_id','topic','in_scope','assigned_subskill','difficulty_rating','target_completion_time','target_quantity','english_glossary','question_bn','answer_options','correct_answer','solution_steps'}
errors=[];warnings=[];loaded={}; codes=set();allq={};alla={}; main_ids=set();review_ids=set()
def error(message):errors.append(message)
def load(name):
    try:
        data=json.loads((ROOT/name).read_text(encoding='utf-8'))
        loaded[name]=data
        return data
    except Exception as exc:
        error(f'{name}: {exc}')
        return None

def norm(value):return ''.join(str(value).casefold().split())
def strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,list):
        for v in value:yield from strings(v)
    elif isinstance(value,dict):
        for v in value.values():yield from strings(v)

for p in ROOT.glob('*.json'):
    if p.name!='validation_report.json':load(p.name)
for prefix in PREFIXES+['review_required']:
    qs=loaded.get(prefix+'_questions.json'); ans=loaded.get(prefix+'_answers.json');is_review=prefix=='review_required'
    if not isinstance(qs,list) or not isinstance(ans,list):error(f'{prefix}: pair must contain arrays');continue
    qids=[q.get('family_id') for q in qs];aids=[a.get('family_id') for a in ans]
    if qids!=aids:error(f'{prefix}: question/answer IDs or ordering do not match')
    for q in qs:
        fid=q.get('family_id'); ctx=f'{prefix}/{fid}'
        if set(q)!=Q_KEYS:error(f'{ctx}: question schema keys differ')
        if fid in allq:error(f'{ctx}: duplicate question ID')
        allq[fid]=q
        (review_ids if is_review else main_ids).add(fid)
        if not re.fullmatch(r'Q\d{3}',str(fid)):error(f'{ctx}: invalid family_id')
        if q.get('in_scope') is not True:error(f'{ctx}: in_scope must be true')
        if not isinstance(q.get('question_bn'),str) or not q['question_bn'].strip():error(f'{ctx}: missing question stem')
        if not isinstance(q.get('answer_options'),list) or len(q['answer_options'])!=4 or not all(isinstance(v,str) and v for v in q['answer_options']):error(f'{ctx}: requires four string options')
        if not isinstance(q.get('english_glossary'),dict):error(f'{ctx}: invalid glossary')
        if not isinstance(q.get('solution_steps'),list) or not all(isinstance(v,str) and v for v in q['solution_steps']):error(f'{ctx}: invalid solution_steps')
        if is_review:
            if q['solution_steps'] or q['difficulty_rating'] is not None or q['target_completion_time'] is not None:error(f'{ctx}: review annotation not withheld')
        else:
            if not q['solution_steps']:error(f'{ctx}: no solution')
            if q['difficulty_rating'] not in ['Easy','Medium','Hard']:error(f'{ctx}: invalid difficulty')
            if not re.fullmatch(r'\d+ seconds',str(q['target_completion_time'])):error(f'{ctx}: invalid completion time')
            if q['correct_answer'] is None:error(f'{ctx}: missing main-file key')
        if q['correct_answer'] is not None and not any(norm(q['correct_answer'])==norm(v) for v in q['answer_options']):error(f'{ctx}: key is not an option')
        if q['correct_answer'] is not None and q['correct_answer'] not in q['answer_options']:warnings.append(f'{ctx}: key/option differs in capitalization or spacing; source spelling retained')
        for text in strings(q):
            for rel in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text):
                if not (ROOT/rel).is_file():error(f'{ctx}: missing image {rel}')
                if not rel.startswith('assets/'):error(f'{ctx}: input references a non-input asset')
    for a in ans:
        fid=a.get('family_id');ctx=f'{prefix}/{fid}'
        if set(a)!={'family_id','possible_mistakes'}:error(f'{ctx}: answer schema keys differ')
        if fid in alla:error(f'{ctx}: duplicate answer ID')
        alla[fid]=a
        if not isinstance(a['possible_mistakes'],list):error(f'{ctx}: mistakes must be an array');continue
        if is_review and a['possible_mistakes']:error(f'{ctx}: review item contains invented mistake traces')
        for m in a['possible_mistakes']:
            required={'type','code','wrong_answer','reasoning_steps'}
            if m.get('type')=='arithmetic':required.add('diverges_at_step')
            if set(m)!=required:error(f'{ctx}: mistake keys differ')
            if m.get('type') not in ['conceptual','arithmetic','interpretation']:error(f'{ctx}: invalid mistake type')
            if m.get('code') in codes:error(f'{ctx}: duplicate mistake code')
            codes.add(m.get('code'))
            steps=m.get('reasoning_steps')
            if not isinstance(steps,list) or not steps or not all(isinstance(s,str) and s for s in steps):error(f'{ctx}: invalid error trace')
            if m.get('type')=='arithmetic' and not (isinstance(m.get('diverges_at_step'),int) and 1<=m['diverges_at_step']<=len(steps)):error(f'{ctx}: divergence out of bounds')
            if fid in allq and norm(m['wrong_answer'])==norm(allq[fid]['correct_answer']):error(f'{ctx}: wrong answer equals key')
            for text in strings(m):
                for rel in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text):
                    if not (ROOT/rel).is_file():error(f'{ctx}: missing mistake image')
index=loaded.get('source_index.json',[]);manifest=loaded.get('manifest.json',{});asset_index=loaded.get('asset_index.json',[])
if {x['family_id'] for x in index}!=set(allq):error('Source index and question IDs do not match')
if set(allq)!=set(alla):error('Global question/answer IDs differ')
if main_ids&review_ids:error('Review IDs leak into topic files')
if len(allq)!=manifest.get('selected_question_count'):error('Manifest selected count mismatch')
if len(main_ids)!=manifest.get('annotated_question_count'):error('Manifest main count mismatch')
if len(review_ids)!=manifest.get('review_required_count'):error('Manifest review count mismatch')
if len(codes)!=manifest.get('hypothetical_mistake_count'):error('Manifest mistake count mismatch')
for x in index:
    if not (ROOT/x['source_evidence_image']).is_file():error('Missing source evidence '+x['family_id'])
    for rel in x['question_images']:
        if not (ROOT/rel).is_file():error('Missing indexed input image '+rel)
for x in asset_index:
    if not (ROOT/x['path']).is_file():error('Missing indexed asset '+x['path'])
report={'passed':not errors,'parsed_json_files':len(loaded),'selected_questions':len(allq),'annotated_questions':len(main_ids),'review_questions':len(review_ids),'mistake_examples':len(codes),'indexed_images':len(asset_index),'errors':errors,'warnings':warnings,'checks':['UTF-8 JSON parsing','exact question and answer schema keys','four options and source-key membership','matching and unique IDs within source','review isolation and withheld generated answers','mistake structure and divergence index','referenced asset existence and input/audit separation','manifest and source-index counts'],'limitations':'Structural validation is not a certification of every source answer or generated pedagogical explanation.'}
(ROOT/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if not errors else 1)
