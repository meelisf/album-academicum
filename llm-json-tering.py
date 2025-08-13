import google.generativeai as genai
import os
import json
import glob
from dotenv import load_dotenv

def create_prompt(record_text, lyhendid_text, json_format_description, few_shot_examples):
    """
    Loob Gemini jaoks prompti, mis sisaldab kogu vajalikku infot.
    """
    prompt = f"""
    Oled abiline, kes teisendab ajaloolisi tekste struktureeritud JSON formaati.
    
    **Ülesanne:** Teisenda järgnev tekstikirje JSON formaati vastavalt allpool toodud kirjeldusele ja näidetele.

    **Sisendteksti formaat:**
    
    Kirjed algavad alati reaga "Immatrikuleerimise kuupäev: ...".
    Seejärel tuleb kirje number kujul "[NR]...".
    Ülejäänud tekst sisaldab informatsiooni isiku, tema õpingute, tegevuse Academia Gustaviana's ja hilisema karjääri kohta.
    Tekstis esineb palju lühendeid. Lühendite tähendused on toodud allpool.
    Esineb palju erandeid ja ebaregulaarsusi teksti struktuuris.
    
    **Nimedest:**
    Mõnedel juhtudel on alguses antud isiku nimeks ainult eesnimi ja patronüüm (isanimest tuletatud nimi), mitte perekonnanimi, eesnimi. 
    Näiteks "Petrus Andreae" tähendab "Peeter, Andrease poeg". Sellisel juhul märgi "family_name" väärtuseks null.

    **Lühendite loend (tering_lyhendid.txt):**
    
    {lyhendid_text}

    **JSON formaadi kirjeldus:**

    ```json
    {json_format_description}
    ```

    **Few-Shot õppe näited:**
    
    {few_shot_examples}

    **Teisendatav tekstikirje:**

    ```
    {record_text}
    ```

    **Väljund (ainult JSON formaadis):**
    """
    return prompt


def process_text_file(file_path, api_key, lyhendid_text, json_format_description, few_shot_examples):
    """
    Töötleb ühte tekstifaili: loeb sisu, genereerib JSONi ja salvestab.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            record_text = f.read()
    except FileNotFoundError:
        print(f"Viga: Faili ei leitud: {file_path}")
        return
    except Exception as e:
        print(f"Viga faili lugemisel: {e}")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = create_prompt(record_text, lyhendid_text, json_format_description, few_shot_examples)

    try:
        response = model.generate_content(prompt)

        if hasattr(response, 'text') and response.text:
            # Eemalda ümbritsevad ```json ja ```, kui need on olemas
            json_output = response.text.strip().replace("```json", "").replace("```", "").strip()

            # Kontrolli, kas väljund on valide JSON
            is_valid = True
            try:
                json.loads(json_output)
            except json.JSONDecodeError:
                is_valid = False
                print(f"Hoiatus: Mudeli väljund ei ole valide JSON: {file_path}")
                print(f"Väljund: {json_output}")

            # Salvesta JSON faili
            filename_without_ext = os.path.splitext(os.path.basename(file_path))[0]
            # Lisa faili nimesse märge, kui JSON ei valideeru
            output_filename = filename_without_ext + ("_INVALID" if not is_valid else "") + ".json"
            output_file_path = os.path.join(os.path.dirname(file_path), output_filename)
            
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                outfile.write(json_output)
            print(f"JSON salvestatud: {output_file_path}")

        else:
            print(f"Viga: Mudel ei tagastanud teksti faili jaoks: {file_path}")

    except Exception as e:
        print(f"Viga API päringus: {e}")



# def process_folder(folder_path, api_key, lyhendid_text, json_format_description, few_shot_examples):
#     """
#     Töötleb kõik tekstifailid antud kaustas.
#     """
#     for filename in os.listdir(folder_path):
#         if filename.lower().endswith('.txt'):
#             file_path = os.path.join(folder_path, filename)
#             process_text_file(file_path, api_key, lyhendid_text, json_format_description, few_shot_examples)

# Uus funktsioon üksiku faili jaoks
def process_single_file(file_path, api_key, lyhendid_text, json_format_description, few_shot_examples):
    """
    Töötleb üksikut tekstifaili.
    """
    if file_path.lower().endswith('.txt'):
        process_text_file(file_path, api_key, lyhendid_text, json_format_description, few_shot_examples)
    else:
        print(f"Hoiatus: {file_path} ei ole tekstifail")

# --- Põhiprogramm ---

# Lae API võti .env failist
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key is None:
    print("Viga: GOOGLE_API_KEY ei ole .env failis määratud.")
    exit()

# Lühendite faili sisu
with open("data/tering_lyhendid.txt", "r", encoding="utf-8") as f:
    lyhendid_text = f.read()

# JSON formaadi kirjeldus failist
try:
    with open("data/json_schema.json", "r", encoding="utf-8") as f:
        json_format_description = json.load(f)
        json_format_description = json.dumps(json_format_description, indent=2) # Ilusamaks
except FileNotFoundError:
    print("Viga: Faili json_schema.json ei leitud.")
    exit()
except json.JSONDecodeError:
    print("Viga: json_schema.json sisu ei ole korrektne JSON.")
    exit()
    

# Few-Shot õppe näited failist
try:
    with open("data/few_shot_examples.json", "r", encoding="utf-8") as f:
        few_shot_examples = json.load(f)
        few_shot_examples = json.dumps(few_shot_examples, indent=2, ensure_ascii=False) # Ilusamaks ja õiged tähed

except FileNotFoundError:
    print("Viga: Faili few_shot_examples.json ei leitud.")
    exit()
except json.JSONDecodeError:
    print("Viga: few_shot_examples.json sisu ei ole korrektne JSON.")
    exit()


# Töötle kausta
#patterns = [
#    "/home/mf/LLM/tering/processed_records/166[0-9]/",
#    "/home/mf/LLM/tering/processed_records/167[0-9]/",
#    "/home/mf/LLM/tering/processed_records/168[0-9]/",
#    "/home/mf/LLM/tering/processed_records/169[0-9]/",
#    "/home/mf/LLM/tering/processed_records/170[0-9]/",
#    "/home/mf/LLM/tering/processed_records/171[0]/",
#]

#for pattern in patterns:
#    for folder in glob.glob(pattern):
#        print(f"Töötan kataloogiga: {folder}")
#        process_folder(folder, api_key, lyhendid_text, json_format_description, few_shot_examples)


# Ja põhiprogrammis:
file_path = "/home/mf/LLM/tering/processed_records/1636/NR214_1636_10.txt"
print(f"Töötan failiga: {file_path}")
process_single_file(file_path, api_key, lyhendid_text, json_format_description, few_shot_examples)
print("Valmis!")
