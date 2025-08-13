import re
import os
from pathlib import Path

def process_month_file(month_file, year):
    """Loeb sisse ühe kuufaili, eraldab kirjed ja tagastab need listina."""
    records = []
    current_record = None
    current_header = None
    
    with open(month_file, 'r', encoding='utf-8') as infile:
        content = infile.read()
        # Eemaldame liigsed tühikud
        content = re.sub(r'\n\s*\n', '\n', content)
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Kuupäeva formaadid
            date_match = re.match(r'^(?:Dep\.\s*)?(\d{1,2})\.\s*(\w+)(?:\s*(\d{4})?)?$', line)
            month_year_match = re.match(r'^(?:Dep\.\s*)?(\w+)\s+(\d{4})$', line)
            
            if date_match:
                day = date_match.group(1)
                month = date_match.group(2)
                year_from_date = date_match.group(3) or year
                current_header = f"{day}. {month} {year_from_date}"
                continue
            elif month_year_match:
                month = month_year_match.group(1)
                year_from_date = month_year_match.group(2)
                current_header = f"{month} {year_from_date}"
                continue
                
            # Uus kirje algab [NR] märgistusega
            if line.startswith('[NR]'):
                if current_record:
                    records.append(current_record)
                nr_match = re.match(r'\[NR\](\d+)', line)
                entry_number = nr_match.group(1) if nr_match else "unknown"
                current_record = {
                    'number': entry_number,
                    'header': current_header,
                    'content': [line]
                }
            elif current_record:
                current_record['content'].append(line)
                
        if current_record:
            records.append(current_record)
            
    return records

def save_records_to_files(records, year, month_str):
    """Salvestab kirjed eraldi failidesse."""
    # Loome väljundkataloogi
    output_dir = Path(f"processed_records/{year}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for record in records:
        if record['header'] and record['content']:
            # Failinimi: [NR]number_aasta_kuu.txt
            filename = f"NR{record['number']}_{year}_{month_str}.txt"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as outfile:
                # Kirjutame päise
                outfile.write(f"Immatrikuleerimise kuupäev: {record['header']}\n\n")
                # Kirjutame sisu
                for line in record['content']:
                    outfile.write(line + "\n")

def process_all_files():
    """Töötleb läbi kõik kuufailid."""
    base_dir = Path("output")
    
    for year_dir in base_dir.glob("*"):
        if not year_dir.is_dir():
            continue
            
        year = year_dir.name
        
        for month_file in year_dir.glob("*.txt"):
            # Võtame kuu numbri failinimest (1691-02.txt -> 02)
            month_str = month_file.stem.split('-')[1]
            
            records = process_month_file(month_file, year)
            save_records_to_files(records, year, month_str)
            print(f"Processed {month_file}")

# Käivitame töötluse
process_all_files()