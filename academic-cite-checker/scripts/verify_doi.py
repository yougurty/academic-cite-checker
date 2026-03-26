#!/usr/bin/env python3
"""
DOI Verification Script using Crossref API
"""
import sys
import json
import urllib.request
import urllib.parse
import ssl

def verify_doi(doi, entry):
    """Verify a single DOI using Crossref API"""
    try:
        # Create SSL context that ignores certificate verification
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}?mailto=academic@cite.checker"
        req = urllib.request.Request(url, headers={'User-Agent': 'AcademicCiteChecker/1.0'})

        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data.get('message'):
                work = data['message']
                result = {
                    'doi': doi,
                    'status': 'found',
                    'title': work.get('title', [''])[0] if work.get('title') else '',
                    'author': '',
                    'year': str(work.get('published-print', {}).get('date-parts', [['']])[0][0]) if work.get('published-print') else str(work.get('published-online', {}).get('date-parts', [['']])[0][0]) if work.get('published-online') else '',
                    'match': False
                }

                # Get first author
                if work.get('author'):
                    first_author = work['author'][0]
                    result['author'] = f"{first_author.get('family', '')}, {first_author.get('given', '')}".strip(', ')

                # Check if title matches (case insensitive, allow small differences)
                entry_title = entry.get('title', '').lower().strip()
                result_title = result['title'].lower().strip()

                # Simple matching: check if main words match
                if entry_title and result_title:
                    entry_words = set(entry_title.split())
                    result_words = set(result_title.split())
                    common_words = entry_words & result_words
                    if len(common_words) >= min(3, len(entry_words)) or result_title in entry_title or entry_title in result_title:
                        result['match'] = True

                return result
            else:
                return {'doi': doi, 'status': 'not_found'}

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'doi': doi, 'status': 'not_found'}
        return {'doi': doi, 'status': 'error', 'message': str(e)}
    except Exception as e:
        return {'doi': doi, 'status': 'error', 'message': str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_doi.py '<JSON array>'", file=sys.stderr)
        sys.exit(1)

    try:
        # Parse the JSON array from command line
        entries = json.loads(sys.argv[1])

        if not isinstance(entries, list):
            print(json.dumps({'error': 'Input must be a JSON array'}))
            sys.exit(1)

        results = []
        for entry in entries:
            doi = entry.get('doi', '')
            if doi:
                result = verify_doi(doi, entry)
                results.append(result)
            else:
                results.append({'doi': '', 'status': 'no_doi'})

        print(json.dumps(results, indent=2))

    except json.JSONDecodeError as e:
        print(json.dumps({'error': f'Invalid JSON: {str(e)}'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
