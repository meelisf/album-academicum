import re

def split_file_by_hundreds(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Leiame "sajaste" alguspunktid (1., 101., 201. jne)
    hundreds_positions = []
    
    # Alustame esimesest kirjest
    pattern = r"^1\."
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        hundreds_positions.append(match.start())
    
    # Leiame ülejäänud "sajased" alguspunktid
    for i in range(101, 2000, 100):  # Eeldame, et kirjeid pole rohkem kui 2000
        pattern = f"^{i}\\."
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            hundreds_positions.append(match.start())
    
    # Jagame failid plokkideks
    for i in range(len(hundreds_positions)):
        start_pos = hundreds_positions[i]
        if i + 1 < len(hundreds_positions):
            end_pos = hundreds_positions[i + 1]
        else:
            end_pos = len(content)
        
        group_content = content[start_pos:end_pos]
        start_number = i * 100 + 1
        end_number = (i + 1) * 100
        
        output_filename = f'/home/mf/Downloads/album_academicum_{start_number}_{end_number}.txt'
        with open(output_filename, 'w', encoding='utf-8') as file:
            file.write(group_content)
        
        print(f"Salvestatud grupp {i+1}: kirjed {start_number}-{end_number}")

# Käivitame jagamise
input_file = '/home/mf/Downloads/album_academicum.txt'
split_file_by_hundreds(input_file)