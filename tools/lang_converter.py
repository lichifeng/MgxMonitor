import os
import re


base_dir = 'D:/SteamLibrary/steamapps/common/AoE2DE/resources'
lang_dirs = [d for d in os.listdir(base_dir) if not d.startswith('_')]

translations = {}
for lang_dir in lang_dirs:
  translations[lang_dir] = {}
  txt_files = os.listdir(os.path.join(base_dir, lang_dir, 'strings', 'key-value'))
  for txt_file in txt_files:
    print(f"Processing {lang_dir}/{txt_file}")
    with open(os.path.join(base_dir, lang_dir, 'strings', 'key-value', txt_file), 'r', encoding='utf-8') as f:
      for line in f:
        match = re.match(r'^(\d+)\s"(.*)"', line)
        if match:
          key, value = match.groups()
          translations[lang_dir][key] = value

lang_src_file = "lang_src.txt"
words = []
with open(lang_src_file, 'r', encoding='utf-8') as f:
  for line in f:
    match = re.search(r'{\d+,\s*"([^"]+)"\}', line)
    if match:
      m = match.group(1)
      words.append(m)
words = set(words)
print(words)

# 步骤4：对于每个非 'en' 的语言，创建一个 .po 文件，将 key 和 value 写入文件。
for lang_dir, trans in translations.items():
  if lang_dir == 'en':
    continue
  po_file_path = f'{lang_dir}.po'
  with open(po_file_path, 'w', encoding='utf-8') as f:
    print(f"Writing {lang_dir}.po")
    cache = {}
    written_words = set()  # 用于存储已经写入的单词
    for word in words:
      for key, value in translations['en'].items():
        if value == word and key not in cache:
          if word not in written_words:  # 只有当这个单词还没有被写入过时，才写入
            cache[key] = translations['en'][key]
            f.write(f'msgid \"{word}\"\n')
            f.write(f'msgstr \"{trans.get(key, "")}\"\n\n')
            written_words.add(word)  # 将这个单词添加到已写入的单词集合中
          
    # for key, value in trans.items():
    #   if key in translations['en'] and translations['en'][key] != value and translations['en'][key] in words:
    #     f.write(f'msgid \"{translations["en"][key]}\"\n')
    #     f.write(f'msgstr \"{value}\"\n\n')

print(len(words))