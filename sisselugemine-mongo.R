install.packages("mongolite")

library(mongolite)


connection <- mongo(collection = "tudengid",
                    db = "album_academicum",
                    url = "mongodb://localhost")

andmed <- connection$find('{}')

# Kõigepealt taastame originaalväärtused
andmed$person$origin$standardized_region <- str_replace_all(
  andmed$person$origin$standardized_region,
  "Schleswig-Schleswig-Holstein-Schleswig-Holstein|Schleswig-Schleswig-Holstein",
  "Schleswig-Holstein"
)

# Siis teeme õige asenduse ühe korraga
schleswig_standariseerimine <- data.frame(
  algne = c(
    "^Schleswig$",  # ^ ja $ tagavad, et asendatakse ainult täpsed vasted
    "^Holstein$"
  ),
  standard = c(
    "Schleswig-Holstein",
    "Schleswig-Holstein"
  )
)

# Teeme asendused
for(i in 1:nrow(schleswig_standariseerimine)) {
  andmed$person$origin$standardized_region <- str_replace_all(
    andmed$person$origin$standardized_region,
    regex(schleswig_standariseerimine$algne[i]),
    schleswig_standariseerimine$standard[i]
  )
}

# Kontrollime tulemust
unikaalsed_regioonid_lõplikud <- sort(unique(andmed$person$origin$standardized_region))
print(unikaalsed_regioonid_lõplikud)