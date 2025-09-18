import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# JSON-faili nimi
failinimi = '/home/mf/LLM/album-amicorum/artikkel/album_academicum.tudengid.json'

try:
    # Lae andmed JSON-failist
    with open(failinimi, 'r', encoding='utf-8') as f:
        andmed = json.load(f)

    # Andmete kogumine: (piirkond, gratulatsioonide arv)
    # Loome listi, kuhu salvestame iga tudengi kohta tema piirkonna grupi
    # ja tema kirjutatud gratulatsioonide arvu.
    kogutud_andmed = []
    for tudeng in andmed:
        # Kasutame .get(), et vältida vigu, kui mõni väli puudub
        piirkonna_grupp = tudeng.get('person', {}).get('origin', {}).get('region_group')
        gratulatsioonid = tudeng.get('academia_gustaviana_activity', {}).get('gratulations', [])
        
        # Lisame andmed listi ainult siis, kui piirkond on teada ja gratulatsioone on
        if piirkonna_grupp and gratulatsioonid:
            kogutud_andmed.append({
                'piirkond': piirkonna_grupp,
                'gratulatsioonide_arv': len(gratulatsioonid)
            })

    # Loome andmetest Pandas DataFrame'i
    df = pd.DataFrame(kogutud_andmed)

    # Rühmitame andmed piirkonna järgi ja liidame gratulatsioonide arvud kokku
    # Seejärel sorteerime tulemused kahanevas järjekorras
    piirkondade_summad = df.groupby('piirkond')['gratulatsioonide_arv'].sum().sort_values(ascending=False)

    # --- Graafiku joonistamine (MUSTVALGE) ---
    
    plt.figure(figsize=(12, 8))

    # Loome horisontaalse tulpdiagrammi, määrates värviks musta
    # edgecolor='white' lisab tulpadele valge ääre, mis võib neid eristada
    bars = plt.barh(piirkondade_summad.index, piirkondade_summad.values, color='black', edgecolor='white')

    # Pöörame y-telje ümber
    plt.gca().invert_yaxis()

    # Lisame arvud tulpade kõrvale
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 3,
                 bar.get_y() + bar.get_height() / 2,
                 f'{width}',
                 va='center',
                 ha='left')

    # Lisame pealkirjad ja sildid
    plt.title('Gratulatsioonide koguarv saatja piirkonna järgi (Piirkondade grupid)', fontsize=16)
    plt.xlabel('Gratulatsioonide koguarv', fontsize=12)
    plt.ylabel('Saatja piirkond', fontsize=12)

    plt.tight_layout()
    plt.show()

except FileNotFoundError:
    print(f"Viga: Faili '{failinimi}' ei leitud.")
except Exception as e:
    print(f"Tekkis viga: {e}")