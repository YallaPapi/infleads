import os
import json
from typing import List

from dotenv import load_dotenv

from src.instantly_integration import InstantlyIntegration, InstantlyLead


def run(emails: List[str], campaign_id: str):
    load_dotenv()
    api_key = os.getenv('INSTANTLY_API_KEY')
    if not api_key:
        raise RuntimeError('INSTANTLY_API_KEY not configured')

    inst = InstantlyIntegration(api_key)

    # Build minimal leads from emails
    leads = []
    for e in emails:
        e = e.strip()
        if not e:
            continue
        leads.append(InstantlyLead(email=e))

    result = inst.add_leads_to_campaign(campaign_id, leads)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    EMAILS = [
        "john@gmail.com",
        "contact@onehourcomfort.com",
        "info@jandjmechanicalservices.com",
        "service@dgacservices.com",
        "jcorish@vkreativ.com",
        "info@interstateac.com",
        "customerservice@themaynardman.com",
        "jcorish@vkreativ.com",
        "service@myersplumbing.com",
        "info@copelandandson.com",
        "ohosseini@turntototal.com",
        "customerservice@solaceservices.com",
        "sales@ecspart.com",
        "info@csheatairelectrical.com",
        "jack@rapidhvactn.com",
        "jcorish@vkreativ.com",
        "nhheatingandcooling@gmail.com",
        "advanced@amctn.com",
        "office@mchnashville.com",
        "sc@air-comfort.com",
        "office@climateprotn.com",
        "nashville@ductdoctor.com",
        "thecleanairco@gmail.com",
        "franklincomfort@gmail.com",
        "info@docair.com",
        "lr.west-nashville@lightspeedrestoration.com",
        "cparks@nstarsvcs.com",
        "office@petittheatingandcooling.com",
        "info@insightac.com",
        "starheatingandac@gmail.com",
        "nick.n@comfortengineered.com",
        "premoairinc@gmail.com",
        "eckertrenovations@outlook.com",
        "jcorish@vkreativ.com",
        "jcorish@vkreativ.com",
        "info@reahvac.com",
        "info@exodusindustries.com",
        "info@hoffmanhydronics.com",
        "apinvoices@superiorincorp.com",
        "jack@rapidhvactn.com",
        "jack@rapidhvactn.com",
        "admin@mahvacservices.com",
        "service@ctechcontrols.com",
        "sales@chillminisplits.com",
        "charlottesales@building-controls.com",
        "office@petittheatingandcooling.com",
        "office@petittheatingandcooling.com",
        "info@airsystemstn.com",
        "service@franklinheatingandcooling.com",
        "nashville@thehayesco.com",
        "sales@insulationsupply.net",
        "contact@thehotwaterheaterpros.com",
        "mark@fminsulation.com",
        "help@varsityzone.com",
        "greenstreethvac@gmail.com",
        "info@proctorandgraves.com",
        "contact@mrcooldirect.com",
        "info@allensaircare.com",
        "liaison@liaisontechgroup.com",
        "info@goicsi.com",
        "chrish@macsinc.com",
        "nashville@crawlspacemedic.com",
        "impallari@gmail.com",
        "smiller@totaltechschool.com",
    ]

    CAMPAIGN_ID = os.getenv('INSTANTLY_TEST_CAMPAIGN') or "6d613d64-51b8-44ab-8f6d-985dab212307"
    run(EMAILS, CAMPAIGN_ID)



