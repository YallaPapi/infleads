import os
import json
import sys
from typing import List, Dict

import pandas as pd

from src.instantly_integration import InstantlyIntegration, convert_r27_leads_to_instantly
from dotenv import load_dotenv


def load_job_result_file(job_id: str) -> str:
    completed_path = os.path.join('data', 'completed_jobs.json')
    if not os.path.exists(completed_path):
        raise FileNotFoundError('completed_jobs.json not found')
    with open(completed_path, 'r') as f:
        data = json.load(f)
    if job_id not in data:
        raise KeyError(f'Job {job_id} not found in completed jobs')
    result_file = data[job_id].get('result_file')
    if not result_file or not os.path.exists(result_file):
        raise FileNotFoundError(f'Result file missing: {result_file}')
    return result_file


def filter_leads_for_instantly(records: List[Dict]) -> List[Dict]:
    out = []
    for r in records:
        email = str(r.get('Email', '')).strip()
        if not email or email == 'NA':
            continue
        status = str(r.get('Email_Status', '')).lower()
        verified_flag = str(r.get('Email_Verified', '')).lower()
        if status == 'valid' or verified_flag in ('true', '1', 'yes'):
            out.append(r)
    # If nothing verified, fall back to any email
    if not out:
        out = [r for r in records if str(r.get('Email', '')).strip() not in ('', 'NA')]
    return out


def main():
    # Load environment variables from .env
    load_dotenv()
    if len(sys.argv) < 3:
        print('Usage: python scripts/send_to_instantly.py <JOB_ID> <CAMPAIGN_ID>')
        sys.exit(1)

    job_id = sys.argv[1]
    campaign_id = sys.argv[2]

    api_key = os.getenv('INSTANTLY_API_KEY')
    if not api_key:
        raise EnvironmentError('INSTANTLY_API_KEY not configured')

    result_file = load_job_result_file(job_id)
    df = pd.read_csv(result_file)
    records = df.to_dict(orient='records')
    filtered = filter_leads_for_instantly(records)
    # Normalize fields to avoid type issues during mapping
    for r in filtered:
        # Ensure SearchKeyword and Location are strings
        sk = r.get('SearchKeyword')
        r['SearchKeyword'] = '' if sk is None or str(sk) == 'nan' else str(sk)
        loc = r.get('Location')
        r['Location'] = '' if loc is None or str(loc) == 'nan' else str(loc)
    instantly_leads = convert_r27_leads_to_instantly(filtered)

    inst = InstantlyIntegration(api_key)
    result = inst.add_leads_to_campaign(campaign_id, instantly_leads)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()


