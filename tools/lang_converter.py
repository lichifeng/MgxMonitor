import os
import re
from datetime import datetime


source_lang = "zh"
fallback_lang = "en"


base_dir = 'D:/SteamLibrary/steamapps/common/AoE2DE/resources'
lang_dirs = [d for d in os.listdir(base_dir) if not d.startswith('_')]

# 读取所有语言的翻译，存到一个很大的字典里面
translations = {}
for lang in lang_dirs:
  translations[lang] = {}
  txt_files = os.listdir(os.path.join(base_dir, lang, 'strings', 'key-value'))
  for txt_file in txt_files:
    print(f"Processing {lang}/{txt_file}")
    with open(os.path.join(base_dir, lang, 'strings', 'key-value', txt_file), 'r', encoding='utf-8') as f:
      for line in f:
        match = re.match(r'^(\d+)\s"(.*)"', line)
        if match:
          id, msg = match.groups()
          translations[lang][id] = msg

# 扫描MgxParser用到的所有单词，英文或中文
lang_src_file = "lang_src2.txt"
words = set()
with open(lang_src_file, 'r', encoding='utf-8') as f:
  for line in f:
    matches = re.findall(r'{\d+,\s*"([^"]+)"\}', line)
    for match in matches:
      words.add(match)
print(f">> Found {len(words)} words")

# 在中文或英文数据中查找对应的ID
# 这儿和上面的总数可能不同，因为不同id可能对应相同的单词，需要做点特殊处理
# 先统计重复的次数，然后再处理
src_dict = {} # id: word
duplicate_count = {} # word: count
for id, msg in translations[source_lang].items():
  if msg in words:
    src_dict[id] = msg
    if msg in duplicate_count:
        duplicate_count[msg] += 1
    else:
        duplicate_count[msg] = 1

#对src_dict按照duplicate_count的值从小到大排序
src_dict = dict(sorted(src_dict.items(), key=lambda item: duplicate_count[item[1]]))
print(f">> Found {len(src_dict)} words in '{source_lang}'")


# 生成其它语言的翻译文件
dir_name = 'out'
if not os.path.exists(dir_name):
    os.makedirs(dir_name)

for lang, trans in translations.items():
  if lang == source_lang:
    continue
  
  po_file_path = f'out/{lang}.po'
  with open(po_file_path, 'w', encoding='utf-8') as f:
    print(f"Writing {lang}.po")
    
    now = datetime.now()
    formatted_now = now.strftime("%Y-%m-%d %H:%M%z")
    f.write(f'''\
msgid ""
msgstr ""
"Project-Id-Version: 1\\n"
"POT-Creation-Date: {formatted_now}\\n"
"PO-Revision-Date: {formatted_now}\\n"
"Last-Translator: Python script\\n"
"Language-Team: Auto generated\\n"
"Language: {lang}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

''')

    translated_words = []
    for id, word in src_dict.items():
      if word in translated_words:
        continue
      translated_words.append(word)
      f.write(f'msgid \"{word}\"\n')
      f.write(f'msgstr \"{trans.get(id, translations[fallback_lang].get(id, word))}\"\n\n')
