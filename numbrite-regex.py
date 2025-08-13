import os
import re

def find_and_mark_entries(filename="data/tering_koondfail.txt"):
    print("Alustan faili lugemist...")
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # List kirjete salvestamiseks koos positsioonidega
    entries = []
    problems = []
    
    # Otsime kõik read, mis algavad numbriga
    # Kasutame otsese otsingu asemel regex otsingut
    current_position = 0
    expected_number = 1
    
    while current_position < len(content):
        # Otsi järgmist rida, mis võiks olla kirje
        pattern = fr'\n{expected_number}\. [A-ZÄÖÜ]'
        match = re.search(pattern, content[current_position:])
        
        if match:
            position = current_position + match.start()
            entries.append((expected_number, position))
            current_position = position + 1
            expected_number += 1
        else:
            problems.append(f"Ei leidnud numbrit {expected_number}")
            expected_number += 1
            if current_position == 0:
                current_position = 1
        
        if expected_number > 1705:  # max number
            break
    
    # Lisa [NR] märgendid
    new_content = content
    offset = 0
    
    for number, position in sorted(entries, key=lambda x: x[1]):
        insert_pos = position + offset
        new_content = new_content[:insert_pos] + '\n[NR]' + new_content[insert_pos+1:]
        offset += 4
    
    print(f"Leitud {len(entries)} kirjet")
    print(f"Probleeme: {len(problems)}")
    
    # Salvesta tulemused
    with open(f"{filename}_marked.txt", 'w', encoding='utf-8') as outfile:
        outfile.write(new_content)
    
    with open(f"{filename}_report.txt", 'w', encoding='utf-8') as outfile:
        outfile.write("\n".join(problems))

def main():
    find_and_mark_entries()

if __name__ == "__main__":
    main()