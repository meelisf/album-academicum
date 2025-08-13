import json
import os
import glob
import requests
import time
import logging
from typing import Dict, Optional, Tuple

# Seadista logimine
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='geonames_update.log',
    filemode='a'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# Geonames API konfiguratsioon
GEONAMES_USERNAME = "aethralis"  # Asenda oma kasutajanimega!
GEONAMES_API_URL = "http://api.geonames.org/searchJSON"

# Ajalooliste nimede ja lühendite teisendused kaasaegseteks nimedeks
HISTORICAL_REGION_MAPPING = {
    "Holstein": "Schleswig-Holstein",
    "Tavastl.": "Häme",
    "Ditmarschen": "Dithmarschen",
    "Lüneburg": "Lüneburg",
    "England": "United Kingdom",
    "Schles.": "Schleswig",
    "Roslagen": "Roslagen",
    "Österreich": "Austria",
    "Rujen": "Rujiena",
    "Eiderstedt": "Eiderstedt",
    "Värml": "Värmland",
    "Curo-Liv": "Kurzeme",
    "Västerbotten": "Västerbotten",
    "Niederlausitz": "Lower Lusatia",
    "Mähren": "Moravia",
    "Schlesien": "Silesia",
    "Vngarus": "Hungary",
    "Savonius/Savolax/(Finnl.)": "Savonia",
    "Bremen": "Bremen",
    "Böhmen": "Bohemia",
    "Oberpfaltz": "Upper Palatinate",
    "Oberpfalz": "Upper Palatinate",
    "Lausitz": "Lusatia",
    "Osnabrück (Westph.)": "Osnabrück",
    "Reval": "Tallinn",
    "Westpr": "West Prussia",
    "Kudbyensis (Östergötl.)": "Östergötland",
    "Savolax": "Savonia",
    "M.": None,  # Puuduv info
    "Riga": "Riga",
    "Germanus": "Germany",
    "Dagö": "Hiiumaa",
    "Tavastensis": "Häme",
    "Savonius/Tavastiensis (Finnl.)": "Häme",
    "Thavastensis": "Häme",
    "Ingermannus": "Ingria",
    "Bayern": "Bavaria",
    "Carelius": "Karelia",
    "Tavastl. (Finnl.)": "Häme",
    "Hungarus Trentsiniensis": "Trenčín",
    "Altmark": "Altmark",
    "Savolax/Wiborg": "Viipuri",
    "Suedus": "Sweden",
    "Estonus": "Estonia",
    "Austro-Finnlander": "Southern Finland",
    "Franken": "Franconia",
    "Svecus": "Sweden",
    "Skåne": "Scania",
    "Blekinge": "Blekinge",
    "Angermannus": "Ångermanland",
    "Bor/ea/-Finl/andus/, (Aland)": "Åland",
    "Jömtl.": "Jämtland",
    "Dalek/arlus/": "Dalarna",
}

# Jälgitav sõnastik Geonames päringute tulemuste salvestamiseks
# See aitab vältida korduvaid API päringuid
GEONAMES_CACHE: Dict[str, Optional[int]] = {}

def search_geonames(region_name: str) -> Optional[int]:
    """
    Otsi Geonames API-st regiooni nime järgi ja tagasta selle Geonames ID.
    
    Args:
        region_name: Regiooni nimi, mida otsida
        
    Returns:
        Geonames ID või None, kui ei leitud
    """
    if not region_name:
        return None
        
    # Kontrolli, kas tulemus on juba vahemälus
    if region_name in GEONAMES_CACHE:
        return GEONAMES_CACHE[region_name]
    
    # Koosta API päring
    params = {
        "q": region_name,
        "featureClass": "A",  # Admin divisions
        "maxRows": 1,
        "username": GEONAMES_USERNAME
    }
    
    try:
        # Lisa väike viivitus, et vältida liiga sagedasi päringuid
        time.sleep(1)
        response = requests.get(GEONAMES_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("totalResultsCount", 0) > 0 and data.get("geonames"):
            geonames_id = int(data["geonames"][0]["geonameId"])
            GEONAMES_CACHE[region_name] = geonames_id
            logging.info(f"Leitud Geonames ID {region_name} jaoks: {geonames_id}")
            return geonames_id
        else:
            logging.warning(f"Ei leitud Geonames ID piirkonnale: {region_name}")
            GEONAMES_CACHE[region_name] = None
            return None
            
    except Exception as e:
        logging.error(f"Viga Geonames API päringul ({region_name}): {str(e)}")
        return None

def get_or_create_geonames_id(region: str) -> Optional[int]:
    """
    Leia regiooni jaoks Geonames ID, kas kaardistusest või API päringuga.
    
    Args:
        region: Algne regiooni nimi
        
    Returns:
        Geonames ID või None, kui ei suudetud leida
    """
    if not region:
        return None
        
    # Teisenda ajalooline nimi kaasaegseks, kui võimalik
    modern_name = HISTORICAL_REGION_MAPPING.get(region)
    
    if modern_name:
        # Otsi Geonames ID kaasaegse nime järgi
        return search_geonames(modern_name)
    else:
        # Proovi originaalnimega, kui kaardistust ei leitud
        return search_geonames(region)

def update_json_files(directory: str, dry_run: bool = True, max_files: int = None) -> Tuple[int, int, int]:
    """
    Uuendab JSON failides standardiseeritud regioonide Geonames ID-sid.
    
    Args:
        directory: Kataloog JSON failidega
        dry_run: Kas ainult näidata muudatusi ilma salvestamata
        max_files: Maksimaalne failide arv, mida töödelda (None = kõik)
        
    Returns:
        Kolmik (uuendatud_failid, vahele_jäetud_failid, vigased_failid)
    """
    # Leia kõik JSON failid
    json_files = glob.glob(os.path.join(directory, "**/*.json"), recursive=True)
    logging.info(f"Leitud {len(json_files)} JSON faili")
    
    if max_files:
        json_files = json_files[:max_files]
        logging.info(f"Töödeldakse maksimaalselt {max_files} faili")
    
    updated_files = 0
    skipped_files = 0
    error_files = 0
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Kontrolli, kas failis on isiku info koos päritoluga
            if 'person' in data and 'origin' in data['person'] and 'standardized_region' in data['person']['origin']:
                region = data['person']['origin']['standardized_region']
                
                # Kui regiooni väärtus on olemas, proovi leida Geonames ID
                if region:
                    # Kontrolli, kas Geonames ID on juba olemas ja korrektne
                    if ('geonames_id' in data['person']['origin'] and 
                        data['person']['origin']['geonames_id'] is not None):
                        skipped_files += 1
                        continue
                    
                    # Otsi Geonames ID
                    geonames_id = get_or_create_geonames_id(region)
                    
                    if geonames_id:
                        # Lisa geonames_id
                        data['person']['origin']['geonames_id'] = geonames_id
                        
                        if not dry_run:
                            with open(file_path, 'w', encoding='utf-8') as file:
                                json.dump(data, file, ensure_ascii=False, indent=2)
                        
                        updated_files += 1
                        logging.info(f"Uuendatud: {file_path}")
                        logging.info(f"  Regioon: {region} -> Geonames ID: {geonames_id}")
                    else:
                        logging.warning(f"Ei leitud Geonames ID regioonile '{region}' failis: {file_path}")
        
        except json.JSONDecodeError:
            logging.error(f"Viga: {file_path} ei ole korrektne JSON fail")
            error_files += 1
        except Exception as e:
            logging.error(f"Viga faili {file_path} töötlemisel: {str(e)}")
            error_files += 1
    
    # Salvesta vahemälu järgmisteks kasutuskordadeks
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geonames_cache.json")
    try:
        with open(cache_path, 'w', encoding='utf-8') as cache_file:
            json.dump(GEONAMES_CACHE, cache_file, ensure_ascii=False, indent=2)
        logging.info(f"Geonames vahemälu salvestatud: {cache_path}")
    except Exception as e:
        logging.error(f"Viga vahemälu salvestamisel: {str(e)}")
    
    return updated_files, skipped_files, error_files

def load_geonames_cache():
    """Laadi eelnevalt salvestatud Geonames vahemälu."""
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geonames_cache.json")
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as cache_file:
                cache = json.load(cache_file)
                GEONAMES_CACHE.update(cache)
                logging.info(f"Laaditud {len(cache)} kirjet Geonames vahemälust")
    except Exception as e:
        logging.error(f"Viga vahemälu laadimisel: {str(e)}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Lisa JSON failidesse Geonames ID-d')
    parser.add_argument('directory', help='Kaust, kus JSON failid asuvad')
    parser.add_argument('--apply', action='store_true', help='Rakenda muudatused (vaikimisi ainult näitab)')
    parser.add_argument('--max-files', type=int, help='Maksimaalne töödeldavate failide arv')
    parser.add_argument('--username', help='Geonames API kasutajanimi')
    
    args = parser.parse_args()
    
    if args.username:
        global GEONAMES_USERNAME
        GEONAMES_USERNAME = args.username
    
    # Laadi eelnevalt salvestatud vahemälu
    load_geonames_cache()
    
    logging.info(f"Töötlen kausta: {args.directory}")
    logging.info(f"Režiim: {'Rakendamine' if args.apply else 'Näitamine'}")
    
    updated, skipped, errors = update_json_files(
        args.directory, 
        dry_run=not args.apply,
        max_files=args.max_files
    )
    
    logging.info(f"\nKokku uuendatud: {updated} faili")
    logging.info(f"Vahele jäetud (juba uuendatud): {skipped} faili")
    logging.info(f"Vigaseid faile: {errors}")
    logging.info(f"Töödeldud kokku: {updated + skipped + errors} faili")

if __name__ == "__main__":
    main()