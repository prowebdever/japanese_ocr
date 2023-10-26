from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path

import os
import json
import numpy as np
import csv
import re

values = [r'(^\d{1,3}((?:,)?\d{3})*(\.\d+)?$)', r'(¥\d{1,3}(?:,\d{3})*(\.\d+)?)', r'(\d{1,3}(?:,\d{3})*(\.\d+)?)(円|万円)', r'(\d{1,3}(?:,\d{3})*(\.\d+)?)(ヶ月|ヵ月|%)', r'(なし|無|ゼロ)$']
keys = ['ソース', '敷金', '礼金', '仲介手数料', '保証料', '火災保険', '鍵交換', '24サポート', '翌月賃料', '概算', 'その他日割り賃料が発生します', '保証料', '駐輪場', '駐車場', 'クリーニング', '消臭除菌・防災セット', '事務手数料', '諸経費', '会員クラブ', '消火剤', '町会費', '水道代', '賃料']

def calculate_distance(element1, element2):
    bottom_diff = element1['bottom'] - element2['bottom']
    left_diff = element1['left'] - element2['left']
    return np.sqrt(bottom_diff**2 + left_diff**2)

def find(line, pattern):
    x = line.rfind(pattern)
    substr = line
    if x > 0:
        substr = line[x:]
    for pt in values:
        match = re.search(pt, substr)
        if match:
            return match.group()
    
    return ''

def extract(file, data):
    temp_path = './temp'
    result_path = './result.csv'

    if os.path.exists(temp_path) == False:
        os.makedirs(temp_path)

    try:
        step1 = data["readResult"]["pages"][0]["lines"]
        step2 = []
        for line in step1:
            rect = line['boundingBox']
            text = line['content'].replace(' ', '')

            addable = False
            for key in keys:
                if key in text:
                    addable = True
            for pt in values:
                x = re.search(pt, text)
                if x:
                    addable = True
                    break

            if addable:
                step2.append({
                    'bottom': rect[7],
                    'left': rect[0],
                    'height': round((rect[7] - rect[1] + rect[5] - rect[3]) / 2),
                    'text': text
                })
        step2.sort(key=lambda k: (k['bottom']))
        
        step3 = []
        bottom = 0
        for part in step2:
            if abs(part['bottom'] - bottom) > 10: # new data
                bottom = part['bottom']
            part['bottom'] = bottom
            step3.append(part)
        step3.sort(key=lambda k: (k['bottom'], k['left']))
        
        temp_file_path = os.path.join(temp_path, file)
        with open(temp_file_path, 'w', encoding='utf-8-sig') as tf:
            json.dump(step3, tf, ensure_ascii=False)

        row = []
        count = len(keys)
        for idx in range(count):
            row.append('')

        row[0] = file

        total_price = 0

        for word in step3:
            text = word['text']
            for idx in range(1, 3):
                x = re.search(values[idx], text)
                if x:
                    value = x.group()
                    price = 0
                    if '¥' in value:
                        price = float(value[1:].replace(',', ''))
                    elif '万円' in value:
                        price = float(value[0:-2].replace(',', '')) * 10000
                    elif '円' in value:
                        price = float(value[0:-1].replace(',', ''))
                    if price > total_price:
                        total_price = price

            for idx in range(1, count):
                if keys[idx] == text:
                    value = ''
                    same_line = [element for element in step3 if element['bottom'] == word['bottom'] and element['left'] > word['left']]
                    if len(same_line):
                        value = find(same_line[0]['text'], keys[idx])
                    if value == '':
                        below_words = [(element, calculate_distance(word, element)) for element in step3 if element['bottom'] > word['bottom']]
                        if len(below_words):
                            below_words.sort(key=lambda x: x[1])
                            value = find(below_words[0][0]['text'], keys[idx])

                    row[idx] = value
        for word in step3:
            text = word['text']
            for idx in range(1, count):
                if row[idx] != '':
                    continue
                if keys[idx] in text:
                    value = find(text, keys[idx])
                    if value == '':
                        same_line = [element for element in step3 if element['bottom'] == word['bottom'] and element['left'] > word['left']]
                        if len(same_line):
                            value = find(same_line[0]['text'], keys[idx])
                    row[idx] = value

        row[-1] = str(round(total_price))

        with open(result_path, 'a', encoding='utf-8-sig', newline='') as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(csvfile)
            
            # writing the data rows
            csvwriter.writerow(row)

    except Exception as err:
        print('Error:', err)

def main():
    source_path = './ocr'
    result_path = './result.csv'

    if os.path.exists(result_path):
        os.remove(result_path)

    with open(result_path, 'w', encoding='utf-8-sig', newline='') as f:
        csvstream = csv.writer(f)
        csvstream.writerow(keys)

    files = os.listdir(source_path)
    
    for org_file in files:
        try:
            path = os.path.join(source_path, org_file)
            with open(path, 'r', encoding='utf-8-sig') as f:
                extract(org_file, json.load(f))
        except Exception as err:
            print('Error:', err)

if __name__ == "__main__":
    main()
