# Digital Curator

#### The Digital Curator application allows you to explore the art collections of Central European museums and search for artworks based on specific motifs.

Users of the application can build their combination of objects and reveal how often the subject has occurred across the centuries, view graphics, drawings, or paintings that represent it in different epochs, and compare data with other themes.

The Digital Curator offers a quantitative view of cultural history based on the frequency of symbols and iconographic themes in many artifacts, not on a detailed observation of individual items. This distant viewing can be especially useful if our interest is aimed at exploring a genre, rather than a specific work, to understand the overall social conditions, rather than the life of a particular artist, or to interpret the overall political situation, rather than the views of the selected author. Exploring big cultural-historical data may bring new insights into abstract social phenomena such as cultural and economic influence, canon issues, the relationship between the center and the periphery, or the functioning of the art market. It can also help us better observe the migration of motifs and their takeover across centuries and distant regions.

The Digital Curator database contains more than 200 000 works from the collections of 100 museums from Austria, Bavaria, the Czech Republic, and Slovakia. The AI ​​library for machine learning TensorFlow and the computer service Google Cloud including the tool Google Cloud Vision were used for the automatic detection of the depicted motifs. Data search and storage is performed using the ElasticSearch database and the operation of the application is provided by the Google App Engine service.

The project was implemented with the kind support of the UMPRUM, Academy of Arts, Architecture and Design in Prague , the Ministry of Education of the Czech Republic, and the Slovak National Gallery . Thanks also go to many museums that made it possible to use their digitized collections, and to Richard Prajer, Radim Hašek, and Eva Škvárová who helped with the development of the application and the preparation of the database.

Lukas Pilka, 2019-2022

## Database structure 

- **acquisition_date**: When and from whom the work was acquired for the museum (E.g.: 1980 from private donation)
- **artist_signature**: Where the signature is placed and what it says (E.g.: Right bottom AD)
- **author**: Who is the author of the work (E.g.: Albrecht Dürer)
- **created_at**: When the database record was created (E.g.: "2020-05-22 09:32:41")
- **date_earliest**: The oldest possible year of creation of the work (E.g.: 1505)
- **date_latest**: The youngest possible year of creation of the work (E.g.: 1506)
- **dating**: Unstructured description of the time of creation of the work (E.g.: Beginning of the 16th century)
- **description**: Curatorial description of the work
- **detected_motifs**: Motifs detected by computer vision
  - **boundBox**: Coordinates defining the boundaries of the motif (E.g.: [0.42,0.58,0.97,0.94])
  - **detector**: Used computer vision model (E.g.: "Resnet V2", "Iconography")
  - **object**: Type of the motif (E.g.: Woman)
  - **score**: Degree of certainty (E.g.: 0.95)
- **gallery**: Name of the museum (E.g.: National gallery in Prague)
- **gallery_url** Url of the artwork in museum's online collection (E.g.: http://sbirky.ngprague.cz/dielo/CZE:NG.O_1552)
- **has_image** Digital reproduction is available (E.g.: true / false)
- **iconography_motifs_updated**: When the computer vision recognition Google Cloud Vision Iconography was performed (E.g.: "2020-05-22 19:12:34")
- **image_id** File name (E.g: "NGP-O1552.jpg")
- **is_free** Is it possible to publish reproduction online (E.g.: true / false)
- **licence** Type of open licence (E.g.: Creative Commons Zero)
- **measurement** Dimensions of the artwork (E.g.: "height 162 cm \ width 192 cm") 
- **medium** Type of material (E.g.: Wood, paper, bronze etc.)
- **original_id** Inventory number of the museum (E.g.: O 1552)
- **place** Geographical location where the artwork was created (E.g.: Venice)
- **resnet_v2_motifs_updated**: When the computer vision TF Resnet V2 was performed (E.g.: "2020-05-22 19:12:34")
- **style** Title of the artwork (E.g.: Feast of the Rosary)
- **topic** Art genre (E.g.: Portrait, Landscape painting etc.)
- **updated_at** When the database record was updated for last time (E.g.: "2021-05-22 09:32:41")
- **work_type** Fine art technique (E.g.: painting, graphic print, drawing etc.)




