import json
import re
from matplotlib.colors import LogNorm, Normalize
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np # Vajalik oodatavate väärtuste arvutamiseks
from collections import Counter

# Andmefaili asukoht
FILE_PATH = '/home/mf/LLM/album-academicum/artikkel/album_academicum.tudengid.json'

def load_data(filepath):
    """Laeb andmed JSON-failist ja tagastab need Pythoni listina."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Edukalt laaditud {len(data)} sissekannet failist {filepath}")
        return data
    except FileNotFoundError:
        print(f"VIGA: Faili ei leitud asukohast: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"VIGA: Fail {filepath} ei ole korrektne JSON-fail.")
        return None

def build_person_database(data, region_key): # Uus parameeter: region_key
    """
    Loob andmebaasi isikutest, kasutades etteantud piirkonna võtit.
    """
    person_db = []
    for entry in data:
        full_name = entry.get('person', {}).get('name', {}).get('full')
        # Kasutame muutujat region_key, et valida õige piirkond
        region = entry.get('person', {}).get('origin', {}).get(region_key)

        if full_name and region:
            person_db.append({'full_name': full_name, 'region': region})
    return person_db

def find_connections_flexible(data, person_db, region_key): # Uus parameeter: region_key
    """
    Leiab seosed, kasutades paindlikku nimeotsingut ja etteantud piirkonna võtit.
    """
    connections = []
    unmatched_names = []
    total_gratulations = 0

    for sender_entry in data:
        # Kasutame muutujat region_key, et valida saatja piirkond
        sender_region = sender_entry.get('person', {}).get('origin', {}).get(region_key)
        gratulations = sender_entry.get('academia_gustaviana_activity', {}).get('gratulations', [])
        
        # Jätame vahele, kui saatjal pole piirkonda või gratulatsioone
        if not sender_region or not gratulations:
            continue

        for gratulation in gratulations:
            total_gratulations += 1
            recipient_name_short = gratulation.get('recipient', {}).get('name')
            if not recipient_name_short:
                continue

            search_terms = re.sub(r'[.,]', '', recipient_name_short).split()
            if not search_terms:
                unmatched_names.append(recipient_name_short)
                continue
                
            found_match = False
            for potential_recipient in person_db:
                full_name = potential_recipient['full_name']
                is_match = all(re.search(r'\b' + re.escape(term), full_name, re.IGNORECASE) for term in search_terms)
                
                if is_match:
                    recipient_region = potential_recipient['region']
                    connections.append({
                        'saatja_piirkond': sender_region,
                        'saaja_piirkond': recipient_region
                    })
                    found_match = True
                    break
            
            if not found_match:
                unmatched_names.append(recipient_name_short)

    # Filtreerime välja ühendused, kus saaja piirkond on None (juhuks kui andmetes on lünki)
    valid_connections = [c for c in connections if c['saaja_piirkond'] is not None]
    return valid_connections, unmatched_names, total_gratulations

# --- UUS FUNKTSIOON ---
def calculate_propensity_matrix(observed_crosstab, all_data, region_key):
    """
    Arvutab kalduvuse (eelistuse) maatriksi, normaliseerides andmed 
    saatjate aktiivsuse ja saajate osakaaluga populatsioonis.
    """
    # 1. Arvutame iga piirkonna osakaalu kogu üliõpilaskonnas
    population_counts = pd.Series([entry['person']['origin'].get(region_key) for entry in all_data]).value_counts()
    population_shares = population_counts / len(all_data)
    
    # 2. Arvutame iga piirkonna poolt saadetud gratulatsioonide koguarvu
    gratulations_sent = observed_crosstab.sum(axis=1)
    
    # 3. Loome oodatavate väärtuste maatriksi
    # Oodatav(A,B) = Saatja_A_saadetud_kokku * Saaja_B_osakaal
    # Kasutame maatriksoperatsioone, et vältida tsükleid
    expected_matrix = pd.DataFrame(np.outer(gratulations_sent, population_shares), 
                                   index=observed_crosstab.index, 
                                   columns=population_shares.index)
    
    # Järjestame veerud, et need vastaksid originaalmaatriksile
    expected_matrix = expected_matrix[observed_crosstab.columns]

    # 4. Arvutame kalduvuse: tegelik / oodatav
    # Lisame väikese väärtuse (epsilon), et vältida nulliga jagamist
    propensity_matrix = observed_crosstab / (expected_matrix + 1e-9)
    
    return propensity_matrix

# Asenda oma vana create_heatmap funktsioon sellega:
def create_heatmap(crosstab_data, title, output_filename, log_scale=False, is_propensity=False, significance_mask=None):
    """Loob risttabelist soojuskaardi ja salvestab selle faili."""
    if crosstab_data.empty:
        print("Risttabel on tühi, soojuskaarti ei looda.")
        return
        
    height = max(8, len(crosstab_data.index) * 0.8)
    width = max(10, len(crosstab_data.columns) * 1.2)
    plt.figure(figsize=(width, height))
    
    # Kalduvusmaatriksi jaoks kasutame teistsugust värviskaalat
    if is_propensity:
        # Kasutame mustvalget värviskaalat vastavalt soovile.
        cmap = "Greys"
        
        # Määrame skaala piirid, et üksikud ekstreemsed väärtused ei rikuks pilti
        # Kõik alla 0.2 on sügavsinine, kõik üle 5 on sügavpunane.
        norm = Normalize(vmin=0, vmax=max(5, crosstab_data.max().max())) 
        
        # Kalduvusmaatriksil kuvame väärtused kahe komakohaga
        # Eemaldatud 'center', kuna 'Greys' ei ole lahknev (diverging) värviskaala.
        heatmap_args = {"annot": True, "fmt": ".2f", "cmap": cmap, "norm": norm}
        print(f"Loome kalduvus-soojuskaardi '{output_filename}'.")

    elif log_scale:
        # Log-skaalal on numbreid annotatsioonidena keeruline kuvada, seega jätame need ära
        heatmap_args = {"norm": LogNorm(), "annot": False, "cmap": "Greys"}
        print(f"Loome soojuskaardi '{output_filename}' logaritmilise värviskaalaga.")
    else:
        # Vaikimisi lineaarne skaala täisarvuliste annotatsioonidega
        heatmap_args = {"annot": True, "fmt": "d", "cmap": "Greys"}
        print(f"Loome soojuskaardi '{output_filename}' lineaarse värviskaalaga.")

    # Lisame maski, et peita statistiliselt ebaolulised väärtused (kui mask on antud).
    # `mask=significance_mask` peidab lahtrid, kus maski väärtus on True.
    # See jätab lahtri tühjaks, selle asemel et kuvada 0.00, mis võiks olla eksitav.
    sns.heatmap(crosstab_data, linewidths=.5, mask=significance_mask, **heatmap_args)
    
    plt.title(title, fontsize=20)
    plt.xlabel('Saaja piirkond', fontsize=14)
    plt.ylabel('Saatja piirkond', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    plt.savefig(output_filename, dpi=300)
    print(f"Soojuskaart on edukalt salvestatud faili: {output_filename}")


def run_analysis(data, region_key, title_prefix, file_suffix):
    print(f"\n{'='*20} ALUSTAN ANALÜÜSI: {title_prefix.upper()} {'='*20}")
    person_db = build_person_database(data, region_key)
    connections, unmatched, total_grats = find_connections_flexible(data, person_db, region_key)
    print(f"\n--- Analüüsi kokkuvõte ({title_prefix}) ---")
    print(f"Gratulatsioone kokku: {total_grats}")
    print(f"Tuvastatud seoseid (saatja-saaja): {len(connections)}")
    if not connections: return
    df = pd.DataFrame(connections)
    crosstab_result = pd.crosstab(df['saatja_piirkond'], df['saaja_piirkond'])
    
    print(f"\n--- Gratuleerimiste sagedusmaatriks ({title_prefix}) ---")
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 120):
        print(crosstab_result)
        
    if region_key == 'region_group':
        create_heatmap(crosstab_result, f'Gratulatsioonide sagedus ({title_prefix})',
                       f'gratulatsioonide_heatmap_{file_suffix}_linear.svg')
        
        create_heatmap(crosstab_result, f'Gratulatsioonide sagedus ({title_prefix}, Log-skaala)',
                       f'gratulatsioonide_heatmap_{file_suffix}_log.svg', log_scale=True)
        
        propensity_matrix = calculate_propensity_matrix(crosstab_result, data, region_key)
        print(f"\n--- Kalduvuse (eelistuse) maatriks (Tegelik/Oodatav) ---")
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 120):
            print(propensity_matrix.round(2))
        
        # --- UUS OSA: LOOME OLULISUSE MASKI ---
        # Määratleme, et seos on "huvitav" ainult siis, kui selle aluseks on vähemalt N gratulatsiooni.
        MIN_GRATULATIONS = 3
        # Mask on `True` nende lahtrite jaoks, mida tahame peita (st mis on alla miinimumi)
        significance_mask = crosstab_result < MIN_GRATULATIONS
        
        # Anname maski edasi heatmap funktsioonile
        create_heatmap(propensity_matrix, f'Gratulatsioonide kalduvus ({title_prefix})\n(Filtriga: vähemalt {MIN_GRATULATIONS} gratulatsiooni)', 
                       f'gratulatsioonide_heatmap_{file_suffix}_propensity_filtered.svg',
                       is_propensity=True,
                       significance_mask=significance_mask)

def main():
    data = load_data(FILE_PATH)
    if not data: return
    run_analysis(
        data=data, 
        region_key='region_group', 
        title_prefix='Piirkondade grupid', 
        file_suffix='region_group'
    )
    print(f"\n{'='*25} ANALÜÜS LÕPETATUD {'='*25}")
    print("Vaata faile:")
    print("- gratulatsioonide_heatmap_region_group_linear.svg")
    print("- gratulatsioonide_heatmap_region_group_log.svg")
    print("- gratulatsioonide_heatmap_region_group_propensity_filtered.svg (UUS: näitab ainult statistiliselt olulisemaid eelistusi)")

if __name__ == "__main__":
    main()