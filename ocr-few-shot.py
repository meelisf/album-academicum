import google.generativeai as genai
import PIL.Image
import os
import time
import threading
import queue
from dotenv import load_dotenv

# --- Funktsioon pildi OCR-imiseks koos uuestiproovimisega ---
def ocr_image(image_path, api_key, examples, max_retries=1, retry_delay=3):
    """
    OCR-ib pildi Gemini API abil, kasutades vestlusajaloo vormis few-shot näiteid
    ja proovides vea korral uuesti.

    Args:
        image_path: Tee pildifailini.
        api_key: Google API võti.
        examples: List sõnastikest, kus iga sõnastik on üks näide.
        max_retries (int): Maksimaalne uuestiproovimiste arv peale esimest katset.
        retry_delay (int): Viivitus sekundites enne uuesti proovimist.
    """
    genai.configure(api_key=api_key)
    # Alustame Flashiga, mis on kiirem ja odavam.
    model = genai.GenerativeModel('gemini-2.5-flash')

    try:
        img = PIL.Image.open(image_path)
    except FileNotFoundError:
        print(f"Viga: Faili ei leitud: {image_path}")
        return None
    except PIL.UnidentifiedImageError:
        print(f"Viga: Ei suutnud pilti avada: {image_path}.")
        return None
    except Exception as e:
        print(f"Viga pildi avamisel {image_path}: {e}")
        return None

    # --- MUUDETUD OSA ALGUS ---

    # Koostame juhised üheks tekstiks
    initial_prompt_text = (
        "Järgi neid reegleid täpselt, et transkribeerida see tekst:\n"
        "1. **Roll:** Sa oled täpne transkribeerija. Sinu ülesanne on ainult transkribeerida tekst etteantud pildifailil.\n"
        "2. **Täpsus:** Kopeeri tekst tähemärgi täpsusega. Säilita kõik algne tekst, lühendid ja kahtlased või vigasena näivad kohad muutumatul kujul.\n"
        "3. **Keelud:** ÄRA paranda arvatavaid kirjavigu. ÄRA moderniseeri keelt. ÄRA lisa omapoolseid kommentaare ega selgitusi ja ÄRA mingil juhul võta few shot näidete teksti transkriptsiooni kaasa. Trankriptsioon peab olema vaid etteantud transkribeeritavast pildifailist.\n"
    )

    # Loome vestluse ajaloo vormis sõnumite listi
    messages = []

    # Lisame näited "user" -> "model" paaridena
    for i, example in enumerate(examples):
        try:
            example_img = PIL.Image.open(example["image"])
            with open(example["text"], "r", encoding="utf-8") as f:
                example_text = f.read()

            # Esimese näitega anname kaasa ka peamised juhised
            if i == 0:
                user_message_parts = [initial_prompt_text, example_img]
            else:
                user_message_parts = [example_img]

            messages.append({'role': 'user', 'parts': user_message_parts})
            messages.append({'role': 'model', 'parts': [example_text]})

        except Exception as e:
            print(f"Hoiatus: Viga näite '{example.get('image', 'N/A')}' töötlemisel: {e}. Jätkan ilma selleta.")

    # Lõpuks lisame päris pildi, mida on vaja transkribeerida, viimase kasutaja sõnumina
    messages.append({'role': 'user', 'parts': [img]})

    # --- MUUDETUD OSA LÕPP ---

    for attempt in range(max_retries + 1):
        try:
            # Vähendame väljundit veidi, et logi oleks selgem
            # print(f"Alustan API päringut failile {os.path.basename(image_path)} (katse {attempt + 1}/{max_retries + 1})...")
            response = model.generate_content(messages)

            if response and hasattr(response, 'text') and response.text:
                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```markdown"):
                    cleaned_text = cleaned_text[len("```markdown"):].strip()
                if cleaned_text.startswith("```"):
                     cleaned_text = cleaned_text[len("```"):].strip()
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-len("```")].strip()

                if cleaned_text:
                    # Edukas päring, ei prindi siin, vaid process_image's
                    return cleaned_text
                else:
                    error_msg = f"Mudel tagastas tühja teksti faili {os.path.basename(image_path)} jaoks (katse {attempt + 1})."

            elif response and hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                error_msg = f"API päring blokeeriti faili {os.path.basename(image_path)} jaoks (katse {attempt + 1}). Põhjus: {response.prompt_feedback.block_reason}"
                print(error_msg)
                return None
            else:
                 error_msg = f"API ei tagastanud oodatud tekstivastust faili {os.path.basename(image_path)} jaoks (katse {attempt + 1}). Vastus: {response}"

            # Prindi veateade ainult siis, kui see pole viimane katse VÕI kui see on viimane katse
            if attempt < max_retries:
                 print(f"{error_msg} Proovin uuesti {retry_delay} sekundi pärast...")
                 time.sleep(retry_delay)
            else:
                 # See prinditakse ainult LÕPLIKUL ebaõnnestumisel
                 print(f"Lõplikult ebaõnnestus peale {max_retries + 1} katset failiga {os.path.basename(image_path)}. Põhjus: {error_msg}")


        except Exception as e:
            error_msg = f"Viga API päringus (katse {attempt + 1}) faili {os.path.basename(image_path)} jaoks: {e}"
            if attempt < max_retries:
                print(f"{error_msg} Proovin uuesti {retry_delay} sekundi pärast...")
                time.sleep(retry_delay)
            else:
                print(f"Lõplikult ebaõnnestus peale {max_retries + 1} katset failiga {os.path.basename(image_path)}. Põhjus: {error_msg}")


    return None # Tagasta None, kui kõik katsed ebaõnnestusid


# --- Funktsioon ühe pildi töötlemiseks ja salvestamiseks ---
# --- MUUDETUD: Tagastab True/False ---
def process_image(image_path, api_key, output_folder, examples):
    """
    Töötleb ühte pilti: OCR ja salvestab teksti faili.
    Tagastab True, kui õnnestus, False kui ebaõnnestus.
    """
    print(f"Alustan töötlemist: {os.path.basename(image_path)}")
    text = ocr_image(image_path, api_key, examples) # Kasutab vaikimisi retries=1

    if text:
        filename_without_ext = os.path.splitext(os.path.basename(image_path))[0]
        txt_filepath = os.path.join(output_folder, filename_without_ext + ".txt")
        try:
            with open(txt_filepath, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Tekst failist {os.path.basename(image_path)} salvestatud: {txt_filepath}")
            print(f"Lõpetasin töötlemise (Edukas): {os.path.basename(image_path)}")
            return True # --- Edukas ---
        except Exception as e:
            print(f"Viga faili kirjutamisel {txt_filepath}: {e}")
            print(f"Lõpetasin töötlemise (Viga kirjutamisel): {os.path.basename(image_path)}")
            return False # --- Ebaõnnestus (kirjutamine) ---
    else:
        # ocr_image tagastas None (pärast võimalikke retries)
        print(f"Pildi {os.path.basename(image_path)} OCR-imine ebaõnnestus lõplikult (ocr_image tagastas None).")
        print(f"Lõpetasin töötlemise (Ebaõnnestus OCR): {os.path.basename(image_path)}")
        return False # --- Ebaõnnestus (OCR) ---


# --- Paralleeltöötluse abifunktsioon (töötaja) ---
# --- MUUDETUD: Lisab ebaõnnestunud failid listi ---
def worker(q, api_key, output_folder, examples, failed_files_list, list_lock):
    """Töötaja funktsioon, mis võtab järjekorrast ülesandeid ja lisab ebaõnnestumised listi."""
    while True:
        try:
            image_path = q.get_nowait() # Võta pildi tee järjekorrast
        except queue.Empty:
            break # Järjekord on tühi, lõpeta töö

        try:
            # Kutsu process_image ja saa teada, kas õnnestus
            success = process_image(image_path, api_key, output_folder, examples)
            if not success:
                # Lisa ebaõnnestunud faili tee listi (kasutades lukku)
                with list_lock:
                    failed_files_list.append(image_path)
        except Exception as e:
            # Püüa kinni ootamatud vead process_image tasemel ja lisa ikkagi listi
            print(f"Ootamatu viga töötlemisel {os.path.basename(image_path)}: {e}")
            with list_lock:
                failed_files_list.append(image_path)
        finally:
            # Veendu, et task_done kutsutakse alati
             try:
                  q.task_done() # Märgi ülesanne tehtuks isegi vea korral
             except ValueError:
                  # Võib juhtuda harvadel juhtudel, kui lõim lõpetab enne task_done kutsumist peale vea püüdmist vms.
                  pass


# --- Funktsioon piltide töötlemiseks kaustast paralleelselt ---
# --- MUUDETUD: Tagastab ebaõnnestunud failide listi ---
def ocr_images_from_folder_parallel(folder_path, api_key, output_folder, examples, num_workers=4):
    """
    Töötleb kõik JPG/PNG pildid antud kaustas paralleelselt kasutades lõimesid.
    Tagastab listi failidest, mille töötlemine ebaõnnestus.
    """
    if not os.path.isdir(folder_path):
        print(f"Viga: Sisendkausta ei leitud: {folder_path}")
        return [] # Tagasta tühi list vea korral

    try:
        os.makedirs(output_folder, exist_ok=True)
    except OSError as e:
        print(f"Viga väljundkausta loomisel {output_folder}: {e}")
        return [] # Tagasta tühi list vea korral

    q = queue.Queue()
    failed_files = [] # List ebaõnnestunud failide kogumiseks
    failed_files_lock = threading.Lock() # Lukk listi kaitsmiseks

    image_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    if not image_files:
        print(f"Kaustast {folder_path} ei leitud töödeldavaid pilte (.jpg, .jpeg, .png).")
        return []

    print(f"Leidsin {len(image_files)} pilti. Alustan töötlemist {num_workers} lõimega...")

    for image_path in image_files:
        q.put(image_path)

    threads = []
    for i in range(num_workers):
        # Anna workerile kaasa list ja lukk
        t = threading.Thread(target=worker, args=(q, api_key, output_folder, examples, failed_files, failed_files_lock), name=f"Worker-{i+1}")
        t.daemon = True
        t.start()
        threads.append(t)

    q.join() # Oota, kuni kõik järjekorras olevad ülesanded on lõpetatud
    print("\nKõik järjekorras olevad ülesanded on lõpetatud.")

    # Tagasta kogutud ebaõnnestunud failide nimekiri
    return failed_files


# --- Põhiprogramm ---
if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("Viga: GOOGLE_API_KEY ei ole keskkonnamuutujates või .env failis määratud.")
        exit(1)

    # --- Seadista siin oma kaustad ---
    image_folder = "/home/mf/LLM/album_academicum/ocr"
    output_folder = "/home/mf/LLM/album_academicum/ocr/transkriptsioon"
    # --- ---

    if not os.path.isdir(image_folder):
        print(f"Viga: Sisendkausta ei leitud: {image_folder}")
        exit(1)

    # --- Few-Shot näited ---
    examples = [
    {
         "image": "/home/mf/LLM/album_academicum/naited/196.jpg",
         "text": "/home/mf/LLM/album_academicum/naited/196.txt"  # Tekstifaili tee
    },   
    ] 

    # --- Käivita OCR paralleelselt ---
    NUMBER_OF_WORKERS = 3 # Kasutad logi järgi 3
    permanently_failed_files = ocr_images_from_folder_parallel(image_folder, api_key, output_folder, examples, num_workers=NUMBER_OF_WORKERS)

    print("\n--- TÖÖTLEMINE LÕPETATUD ---")

    # --- Prindi kokkuvõte ebaõnnestunud failidest ---
    if permanently_failed_files:
        print("\nJärgnevate failide töötlemine ebaõnnestus ka peale uuestiproovimist:")
        for f_path in permanently_failed_files:
            print(f"- {os.path.basename(f_path)} (Tee: {f_path})")
    else:
        print("\nKõikide leitud piltide töötlemine õnnestus!")

    # Hoiatus lõpus on tõenäoliselt endiselt olemas, aga ei tohiks tööd segada
