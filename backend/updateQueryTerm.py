# IMPORTS

import requests
from requests.auth import HTTPBasicAuth
import json
import config
import time

searchedField = 'work_type'

# GET CURRENT TYPES
def getTypesFromElastic():
    queryTypes = {
        "size":0,
        "aggs" : {
            "total" : {
                "terms" : {
                    "field" : searchedField+".keyword",
                    "size": 100
                }
            }
        }
    }

    payload = {'size': 10000}
    rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
                           auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=queryTypes)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    buckets = dataDict['aggregations']['total']['buckets']
    for bucket in buckets:
        print(bucket['key'],bucket['doc_count'])
    print('\n')

# GET DATA FOR EDIT

# work_type
workTypeSubstitutes = [
    {'painting':['akryl','painting2','maliarstvo','malba','Tafelbild (Flügelretabel)','maliarstvo insitné','tempera','Gemälde','obraz','Tafelbild','maliarstvo ľudové','enkaustika','Malerei']},
    {'oil painting':['olej']},
    {'watercolor painting':['akvarel','akvarel koláž tuš','akvarel tempera','kvaš']},
    {'drawing':['kresba', 'Zeichnung','fix','Konturzeichnung','Skizzenbuch']},
    {'charcoal drawing':['uhel','rudka hnědá','rudka podkresba tužkou','sépie lavírovaná','rudka','coal drawing']},
    {'pencil drawing':['pastelka barevná','tužka','pastelka modrá','tužka černá','crayon']},
    {'pastel drawing':['pastel']},
    {'chalk drawing':['křída','křída barevná','křída barevná nesprašná','křídy barevné']},
    {'ink drawing':['perokresba','tuš','pero šedohnědě - podkresba tužkou','rudka tuš běloba','lavírovaná tuš tempera','lavírovaná sépií tuš bistrem','kresba perem tuš','inkoust','perokresba lavírovaná']},
    {'graphic print':['světlotisk','slepotisk','Poster','galvanografie','tisk materiálový, kolorovaný','kamenoryt, barevný','linořez, barevný','linoryt, kolorovaný','tisk materiálový, barevný','sítotisk','linořez','tisk','tisk materiálový','linoryt','linoryt, barevný','Grafik','akvatinta','serigrafie','ofset autorský','serigrafie barevná','monotyp','suchá jehla','tisk z plochy (ofset)','grafika','Grafika','Druck','počítačová grafika','rytina','mezzotinta','heliogravura','mezzotinta (II. stav)','mezzotinta (I. stav)']},
    {'lithography':['litografie']},
    {'etching':['měkký kryt (vernis mou)','lept','lept (II. stav)','lept (I. stav)','lept - mědiryt','lept - akvatinta','lept a mědiryt','lept, suchá jehla']},
    {'copper engraving':['mědiryt','mědiryt a lept','mědiryt - lept']},
    {'woodcut':['dřevoryt','xylografie','dřevořez']},
    {'book':['bibliofília a staré tlače']},
    {'new media':['intermédiá']},
    {'architecture':['architektúra']},
    {'photography':['daguerrotypie','zinkografie','digitální fotografie','fotografia','Fotografie','fotografie','Fotomontage','fotografie kontaktní černobílá','Fotokopie','Film','fotografie černobílá','dokumentárna fotografia','fotografie černobílá zvětšenina','Farbfoto','Fotogramm','fotografie digitální barevná pozitiv']},
    {'applied art':['úžitkové umenie','umelecké remeslo','kov','drevo']},
    {'sculpture':['plastika','skulptura','sochárstvo','Büste','sochárstvo insitné','Münze','Relieftondo','Reiterstatuette','Liegestatuette','Skulptur','Plastik','Sitzstatue','perforace reliéf','Brunnenfigur','Denkmalmodell']},
    {'other':['sépie','perforace','jiná technika, klišé','jiná technika','koláž','mosaika','asambláž','interpretácia','alchymáž','kombinovaná technika','Glasbild']}
]

# gallery
gallerySubstitutes = [
    {'Oblastní galerie Liberec':['Oblastní galerie Liberec  ','Oblastní galerie Liberec ']},
    {'Moravská galerie v Brně':['Moravian Gallery in Brno','Moravská galerie, MG','Moravská galerie v Brně, MG']},
    {'Slovenská národná galéria':['Slovenská národná galéria, SNG']},
    {'Stredoslovenská galéria v Banskej Bystrici':['Stredoslovenská galéria, SGB']},
    {'Galéria mesta Bratislavy':['Galéria mesta Bratislavy, GMB']},
    {'Oravská galéria':['Oravská galéria, OGD']},
    {'Belvedere Museum Wien':['Belvedere Museum Vienna','Österreichische Galerie Belvedere']},
    {'Galerie hlavního města Prahy':['Prague City Gallery']},
    {'Východoslovenská galéria':['Východoslovenská galéria, VSG']},
    {'Považská galéria umenia':['Považská galéria umenia, PGU']},
    {'Galéria umenia Ernesta Zmetáka':['Galéria umenia Ernesta Zmetáka, GNZ']},
    {'Liptovská galéria Petra Michala Bohúňa':['Liptovská galéria Petra Michala Bohúňa, GPB']},
    {'Neue Pinakothek, München':['Bayerische Staatsgemäldesammlungen - Neue Pinakothek, München']},
    {'Šarišská galéria':['Šarišská galéria, SGP']},
    {'Kunsthistorisches Museum Wien':['Kunsthistorisches Museum Vienna']},
    {'Alte Pinakothek, München':['Bayerische Staatsgemäldesammlungen - Alte Pinakothek, München']},
    {'Galéria umelcov Spiša':['Galéria umelcov Spiša, GUS']},
    {'Národní galerie v Praze':['National Gallery in Prague']},
    {'Tatranská galéria':['Tatranská galéria, TGP']},
    {'Galéria Miloša Alexandra Bazovského':['Galéria Miloša Alexandra Bazovského, GBT']},
    {'Pinakothek der Moderne, München':['Bayerische Staatsgemäldesammlungen - Pinakothek der Moderne, München']},
    {'Nitrianska galéria':['Nitrianska galéria, NGN']},
    {'Private collection':['Spišská Sobota. Farský kostol sv. Juraja','Kostol očistovania Panny Márie v Smrečanoch','Ministerstvo vnútra SR - Štátny archív v Banskej Bystrici','Gandy gallery','Politický archív Zahraničného úradu v Berlíne','Rímskokatolícky kostol sv. Petra z Alkantary, Liptovský Mikuláš - Okoličné','Galerie Klatovy / Klenová','Kostol sv. Kríža v Kežmarku','Galerie Pro arte Praha','Opátstvo Jasov','Referenčná zbierka Katedry fotografie a Katedry reštaurovania VŠVU','Rád premonštrátov - Opátstvo Jasov','Galerie Kodl, Praha','Súkromný majetok','Súkromná zbierka','Nezaradená inštitúcia alebo súkromná osoba, NIS','časopis Nové Slovensko','Spišská Kapitula - Katedrála sv. Martina – Kaplnka Zápoľských.']},
    {'Staatsgalerie im Schloss Johannisburg, Aschaffenburg':['Bayerische Staatsgemäldesammlungen - Staatsgalerie im Schloss Johannisburg, Aschaffenburg']},
    {'Památník národního písemnictví':['Památník národního písemnictví, PNP','Památník národního písemnictví, Praha']},
    {'Germanisches Nationalmuseum, Sonja Mißfeldt, Nürnberg':['Bayerische Staatsgemäldesammlungen - Germanisches Nationalmuseum, Sonja Mißfeldt, Nürnberg']},
    {'Bayerische Staatsgemäldesammlungen':['Bayerische Staatsgemäldesammlungen, München']},
    {'Staatsgalerie in der Neuen Residenz, Bernhard Schneider, Bamberg':['Bayerische Staatsgemäldesammlungen - Staatsgalerie in der Neuen Residenz, Bernhard Schneider, Bamberg']},
    {'Neues Schloss Schleißheim, Oberschleißheim':['Bayerische Staatsgemäldesammlungen - Neues Schloss Schleißheim, Oberschleißheim']},
    {'Staatsgalerie in der Katharinenkirche, Augsburg':['Bayerische Staatsgemäldesammlungen - Staatsgalerie in der Katharinenkirche, Augsburg']},
    {'Antimúzeum Júliusa Kollera':['Anti-múzeum Júliusa Kollera, AJK']},
    {'Pinakothek der Moderne Stiftung Ann und Jürgen Wilde, Ann und Jürgen Wilde, München':['Bayerische Staatsgemäldesammlungen - Pinakothek der Moderne Stiftung Ann und Jürgen Wilde, Ann und Jürgen Wilde, München']},
    {'Staatsgalerie im Hohen Schloss Füssen, Füssen':['Bayerische Staatsgemäldesammlungen - Staatsgalerie im Hohen Schloss Füssen, Füssen']},
    {'Staatsgalerie Neuburg, Neuburg':['Bayerische Staatsgemäldesammlungen - Staatsgalerie Neuburg, Neuburg']},
    {'Bayerische Staatsgemäldesammlungen - Staatsgalerie in der Burg zu Burghausen, Burghausen':['Bayerische Staatsgemäldesammlungen - Staatsgalerie in der Burg zu Burghausen, Burghausen']},
    {'Slovenský národný archív':['Slovenský národný archív, Bratislava – fond STK','Slovenský národný archív, Bratislava']},
    {'Neues Schloss Bayreuth, Bayreuth':['Bayerische Staatsgemäldesammlungen - Neues Schloss Bayreuth, Bayreuth']},
    {'Východoslovenské múzeum':['Východoslovenské múzeum, Košice',]},
    {'Slovenské národné múzeum':['Slovenské národné múzeum – Spišské múzeum','Slovenské národné múzeum – Múzeum Bojnice','Slovenské národné múzeum – Etnografické múzeum','Slovenské národné múzeum – Múzeum ukrajinskej kultúry vo Svidníku','Slovenské národné múzeum – Múzeum Betliar','Slovenské národné múzeum – Múzeum Červený Kameň','Slovenské národné múzeum - Múzeum v Martine','Slovenské národné múzeum - archív SNM, Bratislava','Slovenské národné múzeum – Historické múzeum','Slovenské národné múzeum -  Múzeum Slovenských národných rád v Myjave','Slovenské národné múzeum - archív SNM v Bratislave','Slovenské národné múzeum - Historické múzeum, Bratislava','Slovenské národné múzeum -  Múzeum Slovenských národných rád v Myjave']},
    {'Moravské zemské muzeum Brno':['Moravské Zemské Muzeum']},
    {'Benediktinerabtei Ottobeuren, Johannes Schaber OSB, Ottobeuren':['Bayerische Staatsgemäldesammlungen - Benediktinerabtei Ottobeuren, Johannes Schaber OSB, Ottobeuren']},
    {'Slovenské múzeum dizajnu':['Slovenské národné múzeum - Múzeum v Bratislave','Slovenské múzeum dizajnu - SMD, Bratislava']},
    {'Staatsgalerie in der Residenz, Gabriela Wallerer, Ansbach':['Bayerische Staatsgemäldesammlungen - Staatsgalerie in der Residenz, Gabriela Wallerer, Ansbach']},
    {'Vojenský historický archív, Bratislava':['Vojenský historický ústav (VHÚ) - Vojenský historický archív, Bratislava']},
    {'Staatsgalerie in der Residenz, Würzburg':['Bayerische Staatsgemäldesammlungen - Staatsgalerie in der Residenz, Würzburg']},
    {'Univerzitná knižnica v Bratislave':['Univerzitná knižnica v Bratislave - UK BA']},
    {'Magyar Nemzeti Galéria':['Magyar Nemzeti Galéria, Budapešť','Budapest, Szépművészeti Múzeum / Magyar Nemzeti Galéria, Régi Magyar Gyüjtemény','Szépművészeti Múzeum, Budapest – Magyar Nemzeti Galéria']},
    {'Krajské múzeum v Prešove':['Krajské múzeum v Prešove – Kaštieľ Stropkov']},
    {'Kiscelli Múzeum':['BTM, Kiscelli Múzeum – Fővárosi Képtár, Budapest']},
    {'Iparművészeti Múzeum':['Iparművészeti Múzeum, Budapešť']},
    {'Múzeum Slovenského národného povstania':['Múzeum Slovenského národného povstania - múzeum SNP v Banskej Bystrici']},
    {'Museum Brandhorst, München':['Bayerische Staatsgemäldesammlungen - Museum Brandhorst, München']},
    {'Kysucká galéria':['Kysucká galéria, KGC']},
    {'Slovenský filmový ústav':['Slovenský filmový ústav - SFÚ, Bratislava']},
    {'Muzeum města Brna':['Muzeum města Brno']},
    {'Muzeum Auschwitz-Birkenau':['Štátne múzeum Auschwitz – Birkenau v Osvienčime v Poľsku']}
]

def setNewValues(phrasesForReplace):
    for phrasesSet in phrasesForReplace:
        rightPhrase = list(phrasesSet.keys())[0]
        replaceList = []
        for wrongPhrase in phrasesSet[rightPhrase]:
            replaceList.append({"match_phrase": {searchedField: wrongPhrase}})

        ctxScript = "ctx._source."+searchedField+" = '"+ rightPhrase +"'"

        query = {
            "query": {
                "bool": {
                    "should": replaceList
                }
            },
            "script": {
                "inline": ctxScript
            }
        }

        payload = {'size': 10000}
        rawData = requests.post('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_update_by_query',
                               auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
        rawData.encoding = 'utf-8'
        dataDict = json.loads(rawData.text)
        print(rightPhrase + ' - documents updated: '+str(dataDict["updated"]))

setNewValues(workTypeSubstitutes)

time.sleep(1)
print('\n')
print('Current items in '+searchedField+' :')
getTypesFromElastic()
