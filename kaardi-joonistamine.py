import json
import pandas as pd
import folium
from folium.plugins import MarkerCluster

# --- 1. Andmete laadimine ja ettevalmistamine ---

def load_data_from_json(filepath):
    """
    Laeb andmed JSON-failist.
    Sarnane R-i osa: Andmete lugemine andmebaasist või failist.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Edukalt laaditud {len(data)} kirjet failist {filepath}")
        return data
    except FileNotFoundError:
        print(f"VIGA: Faili ei leitud asukohast: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"VIGA: Fail {filepath} ei ole korrektne JSON-fail.")
        return None

def prepare_map_data(data):
    """
    Töötleb toorandmed kaardi jaoks sobivasse formaati.
    Sarnane R-i osa: `data.frame` loomine ja filtreerimine.
    """
    map_points = []
    for entry in data:
        # Kasutame .get() meetodit, et vältida vigu, kui mõni võti puudub
        origin = entry.get('person', {}).get('origin', {})
        if origin:
            coords = origin.get('coordinates', {})
            lat = coords.get('lat')
            lng = coords.get('lng')
            
            # Lisame andmed ainult siis, kui koordinaadid on olemas
            if lat is not None and lng is not None:
                map_points.append({
                    'regioon': origin.get('standardized_region'),
                    'id': origin.get('geonames_id'),
                    'lat': lat,
                    'lng': lng
                })
    
    # Loome pandas DataFrame'i, mis on sarnane R-i andmeraamiga
    df = pd.DataFrame(map_points)

    # Eemaldame read, kus koordinaadid puuduvad (topeltkontroll)
    # Sarnane R-i kood: `kaardi_andmed %>% filter(!is.na(lat) & !is.na(lng))`
    df.dropna(subset=['lat', 'lng'], inplace=True)
    
    return df

def count_students_by_location(df):
    """
    Loendab tudengid asukoha kaupa.
    Sarnane R-i kood: `group_by %>% summarise(arv = n())`
    """
    # Kontrollime, kas veerg 'id' on olemas, enne kui seda grupeerimisel kasutame
    grouping_cols = ['lat', 'lng', 'regioon']
    if 'id' in df.columns:
        grouping_cols.append('id')

    student_counts = df.groupby(grouping_cols).size().reset_index(name='arv')
    return student_counts

def rescale_values(series, new_min=8, new_max=30):
    """
    Skaleerib väärtused uude vahemikku.
    Sarnane R-i kood: `scales::rescale`
    """
    old_min = series.min()
    old_max = series.max()
    
    # Väldime nulliga jagamist, kui kõik väärtused on samad
    if old_max - old_min == 0:
        return pd.Series([new_min] * len(series))
        
    return new_min + (series - old_min) * (new_max - new_min) / (old_max - old_min)

# --- 2. Kaardi loomine ---

def create_map(df):
    """
    Loob Folium kaardi, kasutades püsivat tooltip'i, millel on 
    CSS-i abil eemaldatud vaikimisi taust ja äärised.
    """
    # Määrame markeri suuruse vastavalt tudengite arvule
    df['markeri_suurus'] = rescale_values(df['arv'], new_min=8, new_max=30)
    
    # Loome kaardi, keskpunktiks valime Eesti ligikaudse keskpunkti
    m = folium.Map(location=[58.6, 25.5], zoom_start=7)

    # --- SEE ON UUS JA OLULINE OSA ---
    # Loome CSS-stiili, mis kirjutab üle Leaflet.js-i vaikimisi tooltip'i stiili.
    # Anname oma tooltip'ile unikaalse klassi ('custom-tooltip'), et mitte mõjutada teisi kaardi elemente.
    tooltip_style = """
    <style>
        .leaflet-tooltip.custom-tooltip {
            background-color: transparent;
            border: none;
            box-shadow: none;
            font-weight: bold;
            font-size: 10pt;
            color: white;
            /* Lisame tekstile tugevama varju/piirjoone, et see oleks paremini loetav */
            text-shadow: 
                -1px -1px 0 #000,  
                 1px -1px 0 #000,
                -1px  1px 0 #000,
                 1px  1px 0 #000;
        }
    </style>
    """
    # Lisame loodud CSS-stiili kaardi HTML-i päisesse
    m.get_root().html.add_child(folium.Element(tooltip_style))
    
    # Lisame markerid kaardile
    for idx, row in df.iterrows():
        # Loome popup-i sisu (mis ilmub klikkides)
        popup_html = f"<b>Tudengeid:</b> {row['arv']}<br><b>Regioon:</b> {row['regioon']}"
        
        # Lisame ringikujulise markeri
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=row['markeri_suurus'],
            color="#FF7F00",
            fill=True,
            fill_color="#FF7F00",
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=folium.Tooltip(
                text=str(row['arv']),
                permanent=True,
                direction='center',
                sticky=True,
                # Määrame siin oma CSS-klassi nime
                className='custom-tooltip'
            )
        ).add_to(m)

    return m

# --- Skripti käivitamine ---

if __name__ == "__main__":
    # Määra oma JSON-faili asukoht
    FILE_PATH = 'data/album_academicum.json'
    
    # 1. Lae ja valmista andmed ette
    all_data = load_data_from_json(FILE_PATH)
    if all_data:
        map_data_raw = prepare_map_data(all_data)
        
        # 2. Loenda tudengid asukoha järgi
        student_location_counts = count_students_by_location(map_data_raw)
        
        # 3. Loo kaart
        student_map = create_map(student_location_counts)
        
        # 4. Salvesta kaart HTML-failina
        output_filename = 'tudengite_kaart.html'
        student_map.save(output_filename)
        
        print(f"\nKaart on edukalt salvestatud faili: {output_filename}")
        print("Saate selle faili avada oma veebilehitsejas.")