import re
import os

def process_year_file(year_file, output_base_dir):
    """Jagab aastafaili kirjed kuude kaupa failidesse.
    Eeldab, et iga kuupäev (või kuu ja aasta) tähistab uue kirje algust.
    """
    month_files = {}
    year = os.path.basename(year_file).split('.')[0]
    output_dir = os.path.join(output_base_dir, year)
    os.makedirs(output_dir, exist_ok=True)

    with open(year_file, 'r', encoding='utf-8') as infile:
        current_record = []
        current_month = None

        for line in infile:
            line = line.strip()

            # Regexid kuupäeva ja kuu-aasta jaoks
            date_match = re.match(r'^(?:Dep\.\s*)?\d{1,2}\.\s?(\w+)(?:\s*(\d{4}))?$', line)
            month_year_match = re.match(r'^(?:Dep\.\s*)?(\w+)\s*(\d{4})$', line)

            if date_match or month_year_match:
                # Kirjuta eelmine kirje (kui olemas)
                if current_record:
                    write_record_month(month_files, current_month, current_record, output_dir)
                    current_record = []


                # Uue kuu määramine
                if date_match:
                    month_name = date_match.group(1)
                    year_str = date_match.group(2)
                else:  # month_year_match
                    month_name = month_year_match.group(1)
                    year_str = month_year_match.group(2)


                year_from_date = int(year_str) if year_str else int(year)  # Kui aastat pole, kasuta failinime aastat
                month_number = month_to_number(month_name)

                if month_number is not None and year_from_date == int(year):
                    current_month = f"{year}-{month_number:02}"
                    current_record.append(line)
                #else: # Pole vaja tühjendada, sest alustame uut kirjet nagunii, kui järgmine kuupäev tuleb.
                    # current_record = [] # Ei sobi aasta või kuu


            elif line:  # Lisa KUI RIDA EI OLE TÜHI. See väldib tühjade ridade lisamist.
                if current_record: # Kontrolli, et meil oleks kirje, kuhu lisada!
                    current_record.append(line)


        # Kirjuta viimane kirje
        if current_record:
            write_record_month(month_files, current_month, current_record, output_dir)


    for f in month_files.values():
        f.close()

def write_record_month(month_files, month, record, output_dir):
    """Kirjutab kirje vastava kuu faili."""
    if month is None:
        month = "unknown_month" # Failid ilma kuupäevadeta.
    if month not in month_files:
        filepath = os.path.join(output_dir, f"{month}.txt")
        month_files[month] = open(filepath, 'w', encoding='utf-8')
    month_files[month].write('\n'.join(record) + '\n\n')

def month_to_number(month_name):
    """Teisendab kuu nime numbriks."""
    months = {
        "januar": 1, "jan": 1, "jän": 1,
        "februar": 2, "feb": 2,
        "märz": 3, "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "mai": 5,
        "juni": 6, "jun": 6,
        "juli": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9,
        "oktober": 10, "oct": 10, "okt": 10,
        "november": 11, "nov": 11,
        "dezember": 12, "dec": 12, "desember": 12, "des": 12
    }
    return months.get(month_name.lower(), None)

# --- Põhiprogramm ---
input_base_dir = "output"
for filename in os.listdir(input_base_dir):
    if filename.endswith(".txt"):
        process_year_file(os.path.join(input_base_dir, filename), input_base_dir)

print("Valmis!")