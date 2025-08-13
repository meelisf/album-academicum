import os
import re

class TextToJsonTranslator:
    def __init__(self, max_chunk_size: int = 2500):
        self.max_chunk_size = max_chunk_size

    def read_txt_file(self, filename: str) -> str:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()

    def split_text_into_entries(self, text: str) -> list:
        """
        Jagab teksti loogilisteks tükkideks:
          - Esialgne aastarida (ainult 4-kohaline number) salvestatakse.
          - Seejärel otsitakse "kuupäeva" ridu, mis võivad olla kas täielikud
            (näiteks "20. April 1632") või puuduliku aasta andmetega (näiteks "21. April" või "24. A pril").
          - Kui aasta puudub, lisatakse eelmine teadaolev aasta.
          - Iga kuupäeva alusel jagatakse järgnevad tudengite kirjed (nummerdatud 1., 2., jne).
        """
        chunks = []
        current_year = None

        # Leia rida, mis sisaldab ainult 4-kohalise aasta (nt "1632")
        year_match = re.search(r'^\s*(\d{4})\s*$', text, flags=re.MULTILINE)
        if year_match:
            current_year = year_match.group(1)

        # Muster, mis haarab kuupäeva ridu.
        # See muster haarab ridade alguses: number, punkt, tühik, kuu nimi,
        # ning võimalusel aasta (4 numbrit, võib esineda ka tühikuga enne).
        date_pattern = re.compile(
            r'^\s*(\d{1,2}\.\s+[A-Za-zäöüõÄÖÜÕ]+(?:\s+(\d{4}))?)\s*$',
            flags=re.MULTILINE
        )

        # Leiame kõik kuupäeva read koos asukohtadega tekstis
        date_matches = list(date_pattern.finditer(text))

        # Kui ei leitud ühtegi kuupäeva rida, tagastame tühja loendi
        if not date_matches:
            return chunks

        # Itereerime leidude vahel, et eraldada iga kuupäeva sektsioon
        for i, match in enumerate(date_matches):
            full_date_str = match.group(1).strip()  # näiteks "21. April" või "20. April 1632"
            year_in_date = match.group(2)  # võib olla None, kui aasta puudub

            # Kui aasta puudub, kasuta eelmist teadaolevat aastat
            if not year_in_date:
                if current_year is None:
                    raise ValueError("Aasta pole leitud: veendu, et tekstis oleks rida ainult aasta (nt '1632').")
                full_date_str += f" {current_year}"
            else:
                # Uuenda current_year, kui see on olemas kuupäeval
                current_year = year_in_date

            # Määra sektsiooni alguspositsioon ja lõpp
            section_start = match.end()
            if i + 1 < len(date_matches):
                section_end = date_matches[i+1].start()
            else:
                section_end = len(text)
            section_text = text[section_start:section_end]

            entries = re.split(r'\n\n\s*(?=\d+\.\s+)', section_text)
            # Filtreeri tühjad osad ning eemalda liigsed tühikud
            entries = [entry.strip() for entry in entries if entry.strip()]

            for entry in entries:
                chunks.append({
                    'date': full_date_str,
                    'content': entry
                })

        return chunks

    def save_chunks(self, chunks: list, output_dir: str):
        """Salvesta tükid failidesse"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        for i, chunk in enumerate(chunks, 1):
            output_file = os.path.join(output_dir, f'chunk_{i:03d}.txt')
            content = f"Date: {chunk['date']}\n\n{chunk['content']}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Saved chunk {i} with date {chunk['date']}")

def main():
    # Tee tee skripti asukohast
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'test.txt')
    output_dir = os.path.join(script_dir, 'chunks')

    translator = TextToJsonTranslator()
    text = translator.read_txt_file(input_file)
    chunks = translator.split_text_into_entries(text)
    translator.save_chunks(chunks, output_dir)
    
    print(f"\nCreated {len(chunks)} chunks in directory '{output_dir}'")

if __name__ == "__main__":
    main()
