# Installime vajalikud paketid, kui need pole veel installitud
if (!require("leaflet")) install.packages("leaflet")
if (!require("dplyr")) install.packages("dplyr")

# Laadime paketid
library(leaflet)
library(dplyr)

# Loome andmeraami koordinaatidega
kaardi_andmed <- data.frame(
  regioon = unlist(andmed$person$origin$standardized_region),
  id = unlist(andmed$person$origin$geonames_id),
  lat = unlist(andmed$person$origin$coordinates$lat),
  lng = unlist(andmed$person$origin$coordinates$lng),
  stringsAsFactors = FALSE
)

# Eemaldame puuduvad koordinaadid
kaardi_andmed <- kaardi_andmed %>% 
  filter(!is.na(lat) & !is.na(lng))

# Loendame tudengid asukohtade kaupa
tudengite_arv <- kaardi_andmed %>% 
  group_by(lat, lng, regioon, id) %>% 
  summarise(arv = n(), .groups = "drop")

# Määrame markeri suuruse vastavalt tudengite arvule
# Minimaalne suurus 8, maksimaalne 20
tudengite_arv$markeri_suurus <- scales::rescale(
  tudengite_arv$arv, 
  to = c(8, 30), 
  from = c(1, max(tudengite_arv$arv))
)

# Loome kaardi
m <- leaflet(tudengite_arv) %>%
  addTiles() %>%  
  addCircleMarkers(
    lng = ~lng, 
    lat = ~lat,
    radius = ~markeri_suurus,
    color = "#FF7F00",
    fillColor = "#FF7F00",
    fillOpacity = 0.7,
    weight = 1,
    label = ~as.character(arv),  # Lisame numbri otse kaardile
    labelOptions = labelOptions(
      noHide = TRUE,  # Number on alati nähtav
      direction = "center",
      textOnly = TRUE  # Ainult number ilma taustata
    ),
    popup = ~paste("<b>Tudengeid:</b>", arv, "<br><b>Regioon:</b>", regioon)
  )

# Kuvame kaardi
m