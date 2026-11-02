#!/usr/bin/env python3
"""Generate a prioritized repair queue from the latest Sweeps Titan link audit.
Never overwrites curated entries or guesses destination URLs.
"""
import json,datetime
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'data/link-integrity.json').read_text())
catalog={x['id']:x for x in json.loads((ROOT/'data/sweepstakes.json').read_text())}
priority={'http_error':100,'redirected_to_rules_page':85,'likely_rules_page_not_entry':80,'entry_matches_rules_link':70,'redirected_to_homepage':65,'expired_or_not_found_page':65,'network_check_failed':45,'access_restricted_unconfirmed':30,'no_form_detected_manual_check':20,'redirected_to_other_host':10,'expired_by_listed_end_date':5}
rows=[]
for r in audit['results']:
    item=catalog.get(r['id'])
    if not item:continue
    flags=r.get('issues',[])
    if not flags:continue
    score=max((priority.get(f,1) for f in flags),default=0)
    rows.append({'id':r['id'],'name':r.get('name'),'priority':score,'issues':flags,'httpStatus':r.get('httpStatus'),'currentEntryUrl':item.get('entryUrl'),'officialRulesUrl':item.get('rulesUrl'),'endDate':item.get('endDate'),'reviewStatus':'needs_manual_review'})
rows.sort(key=lambda x:(-x['priority'],x['endDate'] or '9999',x['name'] or ''))
out={'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auditGeneratedAt':audit['generatedAt'],'count':len(rows),'notice':'Research queue only; do not infer a 403 means dead link or automatically promote guessed URLs. Expired records should remain accessible in the expired archive.','queue':rows}
path=ROOT/'data/link-repair-queue.json'
path.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print('Prioritized records:',len(rows),'Top issues:',Counter(f for row in rows for f in row['issues']).most_common(8))
