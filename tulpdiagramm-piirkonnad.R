# Laeme vajalikud paketid (kui pole juba laetud)
# install.packages(c("dplyr", "stringr", "forcats", "ggplot2") install.packages("ggpattern"))

library(dplyr)
library(stringr)
library(forcats)
library(ggplot2)
library(ggpattern)

# Eeldame, et andmestik 'andmed_final' tuleb > mongo-db-andmed-lamedaks.R
# uus_tabel <- select(andmed_final, person_origin_region_group, entry_date)

# Asenda see plokk oma koodis
andmed_grupeeritud <- andmed_final %>%
  
  mutate(uus_grupp = case_when(
    # === MUUDATUS SIIA ===
    is.na(person_origin_region_group) ~ "Muud piirkonnad või piirkond teadmata",
    
    str_detect(person_origin_region_group, "Saksamaa") ~ "Saksamaa (koond)",
    str_detect(person_origin_region_group, "Rootsi") ~ "Rootsi (koond)",
    str_detect(person_origin_region_group, "Soome|Karjala|Ingerimaa") ~ "Soome (koond)",
    person_origin_region_group == "Eesti" ~ "Eestimaa",
    person_origin_region_group == "Liivimaa" ~ "Liivimaa",
    
    # === JA SIIA ===
    TRUE ~ "Muud piirkonnad või piirkond teadmata"
  )) %>%
  
  mutate(aasta = as.numeric(substr(entry_date, 1, 4))) %>%
  filter(!is.na(aasta)) %>% 
  count(aasta, uus_grupp, name = "uliopilaste_arv") %>%
  
  mutate(uus_grupp = fct_relevel(
    uus_grupp, 
    "Liivimaa", "Eestimaa",
    after = Inf
  ))

# Vaatame, milline näeb välja uus, grupeeritud andmestik
print(andmed_grupeeritud)

# Värvid
varvid <- setNames(rep("grey70", length(koik_piirkonnad)), koik_piirkonnad)
varvid["Liivimaa"] <- "red3" 
varvid["Eestimaa"] <- "red4"   
varvid["Soome (koond)"] <- "purple4"
varvid["Saksamaa (koond)"] <- "forestgreen"
varvid["Rootsi (koond)"] <- "steelblue1"

varvid["Muud piirkonnad või piirkond teadmata"] <- "gray90"

# Joonistame graafiku
ggplot(data = andmed_grupeeritud, 
       aes(x = aasta, y = uliopilaste_arv, fill = uus_grupp)) +
  geom_col(color = "white", linewidth = 0.2) +
  
  scale_fill_grey(start = 0.9, end = 0.2) + 
  
  labs(
    title = "Immatrikuleeritute arv (piirkonnad grupeeritud)",
    subtitle = "Saksamaa, Soome ja Rootsi piirkonnad on koondatud",
    x = "Aasta",
    y = "Üliõpilaste arv",
    fill = "Päritolugrupp"
  ) +
  theme_minimal() +
  scale_x_continuous(breaks = seq(1632, 1710, by = 2)) +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "bottom"
  )