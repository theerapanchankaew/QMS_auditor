"""Exact, hash-bound clause retrieval for the supplied controlled PDF. No network."""
from pathlib import Path
import hashlib
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'assets/manifests/runtime-source-registry.json'

class ReferenceGap(ValueError):
    pass


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ClauseStore:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.registry = json.loads((self.root / 'assets/manifests/runtime-source-registry.json').read_text())
        self.source = self.registry['primary_standard']
        self.path = (self.root / self.source['path']).resolve()
        if not self.path.is_relative_to(self.root) or not self.path.is_file():
            raise ReferenceGap('Controlled PDF missing or outside package')
        if sha256(self.path) != self.source['sha256']:
            raise ReferenceGap('Controlled PDF hash changed: review source and rebuild registry before use')
        profiles = self.root / 'assets/requirement_profiles'
        index = json.loads((profiles / '_index.json').read_text())
        self.profiles = {x['clause']: json.loads((profiles / (x['clause']+'.json')).read_text()) for x in index['clauses']}
        numbers = set(self.profiles)
        for n in list(numbers):
            parts=n.split('.')
            numbers.update('.'.join(parts[:i]) for i in range(1,len(parts)))
        lines=[]
        eligible=set()
        with fitz.open(self.path) as doc:
            for page_number in range(self.source['body_start_page'],self.source['body_end_page']+1):
                page=doc[page_number-1]
                # Preserve PDF text order, excluding only page header/footer by coordinates.
                for block in page.get_text('dict')['blocks']:
                    for line in block.get('lines',[]):
                        if line['bbox'][1] < page.rect.height*0.065 or line['bbox'][3] > page.rect.height*0.94:
                            continue
                        text=''.join(s['text'] for s in line['spans']).strip()
                        if text:
                            correction=self.source.get('heading_corrections',{}).get(f'{page_number}:{text}')
                            if line['bbox'][0] < page.rect.width*0.10:
                                eligible.add(len(lines))
                            lines.append((page_number,correction or text))
        headings=[]
        for pos,(page,text) in enumerate(lines):
            match=re.fullmatch(r'((?:[4-9]|10)(?:\.\d+){0,3})\.?(?:\s+(.*))?',text)
            if pos in eligible and match and match[1] in numbers:
                headings.append((match[1],pos,page))
        found=[x[0] for x in headings]
        missing=set(self.profiles)-set(found)
        duplicates={n for n in found if found.count(n)>1}
        if missing or duplicates:
            raise ReferenceGap(f'Heading integrity failed: missing={sorted(missing)}, duplicate={sorted(duplicates)}')
        if [tuple(map(int,n.split('.'))) for n in found] != sorted(tuple(map(int,n.split('.'))) for n in found):
            raise ReferenceGap('Heading order is not monotonic')
        self.clauses={}
        for idx,(number,start,page) in enumerate(headings):
            level=number.count('.')
            end=next((h[1] for h in headings[idx+1:] if h[0].count('.')<=level),len(lines))
            text='\n'.join(t for _,t in lines[start:end])
            if number in self.profiles and (len(text)<60 or 'shall' not in text.lower()):
                raise ReferenceGap(f'Clause {number} has no credible requirement body')
            self.clauses[number]={'source_id':self.source['source_id'],'source':self.source['path'],
                'source_sha256':self.source['sha256'],'clause':number,
                'start_page':page,'end_page':lines[end-1][0],'text':text,
                'title':self.profiles.get(number,{}).get('clause_title',number),
                'evidence_bucket':'primary','text_status':'PDF text layer; not a full OCR accuracy certification'}

    def get(self, clause):
        if clause not in self.clauses:
            raise ReferenceGap(f'Clause {clause} is not in the registered normative body')
        return dict(self.clauses[clause])

    def context(self, clause, assessment=False):
        primary=self.get(clause)
        profile=self.profiles.get(clause)
        names=['governance/closed-source-policy.md','governance/evidence-integrity-rules.md']
        if assessment:
            names += self.registry['assessment_rules']
        refs=[]
        for name in names:
            p=self.root/'references'/name
            if not p.is_file():raise ReferenceGap(f'Missing rule: {name}')
            refs.append({'source':str(p.relative_to(self.root)),'sha256':sha256(p),'text':p.read_text()})
        return {'primary':primary,'profile':profile,'rules':refs,'human_release_required':True}
