###################################################################
# OSA parser : script to parse nexus txns using OSA's mapping 
# Ravi, 17th June 2025
###################################################################

import json
import textdistance
MODEL = 'jaro_winkler'
MIN_SIMILARITY = 0.9
f_dist: textdistance.algorithms.base.BaseSimilarity = getattr(textdistance, MODEL)

first_value = lambda non_iterable: next(iter(non_iterable))

def load_payload(payload_path:str):
    """Loads json file at payload_path:str"""
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    return payload

def path_join(prefix:str, suffix:str):
    if suffix.startswith('='):
        return prefix + suffix
    else:
        return '/'.join([prefix, suffix])

# fuzzy_match = lambda tokens, target: max(tokens, key=lambda s: f_dist.normalized_similarity(s, target))
def fuzzy_match(tokens:list[str], target:str):
    scores = [f_dist.normalized_similarity(t.lower(), target.lower()) for t in tokens]
    max_score = max(scores)
    if max_score < MIN_SIMILARITY:
        return None
    else:
        return tokens[scores.index(max_score)]

def traverse_xpath(xpath:str, payload, show_result=False, hide_errors=False):
    """
    Recursive function that traverses through a payload given xpath 
    returns all mathcing xpaths in payload as a list[str]
    """
    if xpath:
        if '/' in xpath:
            slash_idx = xpath.index('/')
            xpath_key = xpath[:slash_idx]
            xpath_key_lowercase = xpath_key.lower()
            next_xpath = xpath[slash_idx+1:]
        else:
            xpath_key = xpath
            xpath_key_lowercase= xpath_key.lower()
            next_xpath = ''
        # match with payload keys: 
        if isinstance(payload, dict):
            payload_keys = list(payload.keys())
            payload_key_match = fuzzy_match(payload_keys, xpath_key)
            if payload_key_match:
                next_payload = payload[payload_key_match]
                return [path_join(payload_key_match, next_result) for next_result in traverse_xpath(next_xpath, next_payload, show_result, hide_errors)] # tested
            else:
                if xpath_key_lowercase=='*':
                    if payload:
                        # payload_key, next_payload = next(iter(payload.items()))
                        # return '/' + payload_key + traverse_xpath(next_xpath, next_payload)
                        result = []
                        for payload_key, next_payload in payload.items():
                            for next_result in traverse_xpath(next_xpath, next_payload, show_result, hide_errors):
                                result.append(path_join(payload_key, next_result))
                        return result
                    else:
                        if hide_errors:
                            return []
                        else:
                            return [': End of branch'] # tested
                else:
                    if hide_errors:
                        return []
                    else:
                        return [xpath_key + ': Key not found'] # tested.
        elif isinstance(payload, list):
            # search key in each element of list
            result = []
            for idx, next_payload in enumerate(payload):
                # assuming that the next_payload is an dict
                for next_result in traverse_xpath(xpath, next_payload, show_result, hide_errors):
                    result.append(f'[{idx}]/' + next_result)
            return result
        else:
            if hide_errors:
                return []
            else:
                return [xpath_key + ': Path is longer than branch'] # tested.
    else:
        if show_result:
            return ['=\n'+json.dumps(payload, indent=4)]
        else:
            if isinstance(payload, list):
                if payload:
                    return ['=<array>']
            if isinstance(payload, dict):
                if payload:
                    return ['=<json>']
            return ['='+str(payload)] # tested

def extract(xpath:str, payload):
    results = traverse_xpath(xpath, payload, show_result=True, hide_errors=True)
    payloads = {}
    for res_str in results:
        idx = res_str.index('\n')+1
        payloads.update(
            {
                res_str[:idx-2]: json.loads(res_str[idx:])
            }
        )
    return payloads

def xpath_filter(xpaths_to_filter:list[str], filtering_xpaths:list[str], payload):
    # first get filters.
    # search for xpath in payloads and filter results where =value appears
    # collect the correct path upto last array indices.
    filters = []
    results = []
    for f_x in filtering_xpaths:
        if len(f_x.split('=')) != 2:
            # print(f'Invalid filtering condition:\n{f_x}')
            results.append(f'Invalid filtering condition:\n{f_x}')
            continue
        f_xpath, f_val = f_x.split('=')
        f_res = [f for f in traverse_xpath(f_xpath, payload) if f.endswith(f'={f_val}')]
        
        if not f_res:
            results.append(f'{f_x} does not exist')
            return results
        
        results += f_res
        for f in f_res:
            idx = f.rfind(']')+1
            filters.append(f[:idx])
    
    # if you are here, filters are correct.
    
    for xp in xpaths_to_filter:
        # xp should have all the filtering conditions.
        for f_xp in traverse_xpath(xp, payload):
            if all(f_xp.startswith(f) for f in filters):
                results.append(f_xp)
    return results

def parse_mapping(nexusPaths:str, payload):
    nexusPathsSplit = nexusPaths.strip().splitlines()
    filterPaths = [path for path in nexusPathsSplit if '=' in path]
    xpaths      = [path for path in nexusPathsSplit if '=' not in path]
    return '\n'.join(xpath_filter(xpaths, filterPaths, payload))

# def parse_v(nexus_paths, payload):
#     analyses_str_v = []
#     for key in nexus_paths:
#         analyses = parse(key, payload)
#         analyses_str_v.append(str(analyses).replace(',', ',\n'))
#     return analyses_str_v

# import os 
# import pandas as pd
# import openpyxl
# from openpyxl.cell.rich_text import CellRichText, TextBlock
# from openpyxl.worksheet.cell_range import CellRange

# def load_open_workbook(filepath, striked=True):
    
#     # read even when file is open coz nobody can stahp meh
#     if not os.path.exists('temp'):
#         os.makedirs('temp')
    
#     os.system(f'xcopy /Y "{filepath}" temp\\ > nul')
#     filename = os.listdir('temp')[0]
#     newPath = 'temp\\' + filename

#     if striked:
#         df_dict = pd.read_excel(newPath, sheet_name=None, dtype=str)
#     else:
#         df_dict = {}
#         book = openpyxl.load_workbook(newPath, rich_text=True)
#         for sheet in book.sheetnames:
#             worksheet = book[sheet]
#             active_range = CellRange(worksheet.calculate_dimension())
#             max_row = active_range.max_row
#             max_col = active_range.max_col
#             header = [worksheet.cell(1, i+1).value for i in range(max_col)]
#             data = []
#             for row in worksheet.iter_rows(2, max_row, 1, max_col):
#                 row_data = []
#                 for cell in row:
#                     cell_data = ''
#                     if isinstance(cell.value, CellRichText):
#                         for text in cell.value:
#                                 if isinstance(text, TextBlock):
#                                     if not text.font.strike:
#                                         cell_data += str(text)
#                                 else:
#                                     cell_data += str(text)
#                     else:
#                         cell_data = str(cell.value)
#                     row_data.append(cell_data)
#                 data.append(row_data)
#             df_dict.update({sheet: pd.DataFrame.from_records(data, columns=header)})
#         book.close()
#     os.remove(newPath)
#     return df_dict