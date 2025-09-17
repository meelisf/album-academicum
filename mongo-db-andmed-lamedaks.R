library(tidyverse)

# See abifunktsioon kontrollib, kas veerg on olemas ja kas see on list,
# enne kui proovib seda lahti pakkida.
safe_unnest <- function(df, col_name, sep = "_") {
  # Kui veergu pole olemas või see pole list, tagasta andmestik muutmata
  if (!col_name %in% names(df) || !is.list(df[[col_name]])) {
    return(df)
  }
  
  # Kui on, siis paki lahti
  tidyr::unnest_wider(df, all_of(col_name), names_sep = sep)
}

# 1. Koosta nimekiri KÕIKIDEST veergudest, mida tahad lahti pakkida,
# alustades kõige välimisest kihist.
veerud_lahtipakkimiseks <- c(
  "person",
  "person_name",
  "person_origin",
  "person_birth",
  "person_death",
  "person_father",
  "person_relations",
  "person_name_birth",
  "person_name_death"# Lisame ka selle siia igaks juhuks
  # Lisa siia teisi, kui avastad neid veel
)

# 2. Kasuta purrr::reduce, et rakendada safe_unnest funktsiooni järjest
# igaühele neist veergudest.
andmed_final <- purrr::reduce(
  veerud_lahtipakkimiseks, 
  .f = safe_unnest, 
  .init = andmed
)

# Kontrolli lõpptulemust
glimpse(andmed_final)
colnames(andmed_final)