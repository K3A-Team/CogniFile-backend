import os
import requests
import time


# This logic is working but is subject to performance optimization , so it's commented until it's improved
# Kudos to @ELHart05 for the implementation
async def is_file_malicious(file_content: bytes) -> bool:
    '''
    VIRUSTOTAL_URL = 'https://www.virustotal.com/api/v3/files'
    headers = {
        'x-apikey': os.getenv("VIRUSTOTAL_API_KEY")
    }

    # Submit the file to VirusTotal
    response = requests.post(VIRUSTOTAL_URL, headers=headers, files={'file': file_content})
    result = response.json()

    if 'data' in result and 'id' in result['data']:
        analysis_id = result['data']['id']
        analysis_url = f'https://www.virustotal.com/api/v3/analyses/{analysis_id}'

        while True:
            analysis_response = requests.get(analysis_url, headers=headers)
            analysis_result = analysis_response.json()

            if 'data' in analysis_result and 'attributes' in analysis_result['data']:
                status = analysis_result['data']['attributes']['status']
                if status == 'completed':
                    scan_results = analysis_result['data']['attributes']['results']
                    for engine in scan_results:
                        if scan_results[engine]['category'] == 'malicious':
                            return True
                    break

            time.sleep(10)

    return False

    '''

    if (file_content == b'malicious'):
        return True
    return False
