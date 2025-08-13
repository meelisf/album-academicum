import os
import re

def merge_hyphenations(text):
    """Liidab poolitatud sõnad."""

    def replace_hyphenation(match):
        # See funktsioon saab re.sub poolt leitud vaste
        first_part = match.group(1)  # Sõnaosa koos sidekriipsuga
        next_line_start = match.group(2) #järgmine rida
        return first_part.replace("-", "") + next_line_start #eemaldab sidekriipsu

    #  Otsib sõna, mis lõpeb sidekriipsuga, millele järgneb
    #  reavahetus (võimalike tühikutega) ja väiketähega algav sõna.
    pattern = r'(\w+-)\s*\r?\n\s*([a-zäöüõ][^\s]*)'
    
    # Kasutame re.sub koos asendusfunktsiooniga.
    cleaned_text = re.sub(pattern, replace_hyphenation, text, flags=re.MULTILINE)
    return cleaned_text


def process_files(root_dir):
    """Liidab poolitatud sõnad kõigis failides."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames.sort()
        filenames.sort()
        for filename in filenames:
            if filename.endswith('.txt'):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    cleaned_content = merge_hyphenations(content) # Teeb liitmise

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)  # Kirjutab muudetud teksti tagasi faili

                    print(f"Poolitused liidetud: {file_path}")
                except Exception as e:
                    print(f"Viga faili {file_path} töötlemisel: {str(e)}")

root_directory = '/home/mf/LLM/tering/processed_records/'  # Asenda oma kataloogiteega
process_files(root_directory)