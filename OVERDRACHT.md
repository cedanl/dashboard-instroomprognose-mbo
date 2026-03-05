# 📊 Overdracht en suggesties voor verbetering

De huidige versie van deze repository is een eerste opzet voor het visualiseren van de CAMBO data en instroomprognose op deze data. Onderstaand wordt toegelicht wat de status van dit project bij overdracht is. Daarnaast zullen suggesties voor vebetering en benodigdheden voor in productiename, beschreven worden.
...




## Actiepunten en wensen en ideeën
- [ ] Pacakage optimaliseren, door alle bestanden en mappen weg te gooien die niet gebruikt worden.
- [ ] inschrijvingen per week van voorgaande jaren in dezelfde periode koppelen (kan dit op basis van CAMBO data of SIS data)
- [ ] Pipeline om data uit andere packages in te kunnen lezen / koppelen
- [ ] In overleg met eindgebruikers verbeteren en uitbreiden van visuals waar wenselijk.
- [ ] Validatie visual met betrouwbaarheidsindex van de voorspelling.
- [ ] Hosten van Streamlit app binnen een organisatie.

Samenvoegen van de drie losse onderdelen uit dit project tot één werkende package, namelijk
1 – data analyse en preparen CAMBO data,
2 – prognose model draaien en output creëren en
3 – visualisatie van de CAMBO data en visualisatie van de prognose uitkom
Of de optie dat package 1 t/m 3 op de een of andere manier aan elkaar gekoppeld kunnen worden of dat de bestanden makkelijk op te halen zijn (via Streamlit aanroepen van package 1 en 2 o.i.d.?).
Uitbreiding databronnen, zoals PortalPlus en SIS (inschrijf)data.
Namen personen op te vragen bij auteur 
KeyUser groep
Namen eventuele uit te nodigen personen op te vragen bij de auteur


## Uidagingen
- [ ] Input afhankelijk van twee andere repository's. De twee input repository's zullen eerst gedraaid moeten worden, voordat je goede input hebt voor deze repository. Dus er moeten drie repository's werkend gekregen worden. Dit is niet wenselijk.
- [ ] CAMBO data éénmaal per jaar, na afloop van studiejaar. Wenselijk zou zijn als data ook tijdens lopende jaar op te vragen zijn.
- [ ] Het gebruiken van de in deze ontwikkelde reposiroy app is waarschijnlijk te technisch om op grote schaal in gebruik te nemen. Eén van de oplossingsrihtingen zou het hosten van Streamlit app binnen een organisatie kunnen zijn. Daarnaast zou een pipeline, die de data van de twee afhankelijke repository's ophaalt en verolgens deze repository draait, wenselijk zijn.





# 📊 Projectoverdracht – Visualisatie en prognose op basis van CAMBO-data

## 1. Inleiding

Deze repository bevat een eerste prototype voor het analyseren en visualiseren van CAMBO-data en het genereren van instroomprognoses op basis van deze data.

Het doel van dit project is om inzicht te bieden in historische instroom en om toekomstige instroom te kunnen voorspellen, waarbij de resultaten beschikbaar worden gemaakt via een interactieve visualisatie (Streamlit).

Dit document beschrijft:

* de huidige status van het project bij overdracht
* mogelijke verbeteringen en uitbreidingen
* technische en organisatorische aandachtspunten voor verdere ontwikkeling en eventuele productiename.

---

# 2. Huidige projectstructuur

Het project visuatliseert data die voortkomen uit twee andere CEDA-packagesn namelijk:

1. CAMBO data (https://github.com/cedanl/instroomprognose-mbo) en
2. Studentprognose model van de Radboud Universiteit (https://github.com/cedanl/studentprognose)bestaat momenteel uit drie afzonderlijke onderdelen:

### 1. Data-analyse en voorbereiding van CAMBO-data

In dit onderdeel wordt de CAMBO-data ingelezen, geanalyseerd en voorbereid voor verdere verwerking.

Belangrijke activiteiten:

* opschonen van data
* structureren van relevante variabelen
* voorbereiden van data voor gebruik in het prognosemodel

### 2. Prognosemodel

Op basis van de voorbereide data wordt een prognosemodel uitgevoerd dat een voorspelling doet van de toekomstige instroom.

Output van dit onderdeel:

* voorspelde instroomwaarden
* modeloutput die gebruikt kan worden voor visualisatie

### 3. Visualisatie

De resultaten uit de twee andere repository's worden gevisualiseerd in een Streamlit-applicatie.

De applicatie biedt onder andere:

* inzicht in historische CAMBO-data (deze is nog in ontwikkeling, overweging is om de visluaties uit instroomprognose-mbo
repository in deze app te integreren.)
* visualisatie van instroomprognoses
* interactieve weergave van trends en ontwikkelingen

Momenteel functioneren deze drie repository's nog los van elkaar.

---

# 3. Actiepunten en verbetermogelijkheden

## 3.1 Technische verbeteringen

* De drie onderdelen van het project samenvoegen tot één geïntegreerd package:

  * data-analyse en datavoorbereiding
  * prognosemodel
  * visualisatie

Een alternatief is het koppelen van de onderdelen via een duidelijke workflow of pipeline, zodat zij eenvoudig data van elkaar kunnen ophalen.

Indien de repository's los van elkaar blijven functioneren, is het wenselijk om:

* een pipeline te ontwikkelen waarmee data uit andere packages automatisch kunnen worden ingelezen in de streamlit app;
* een pipeline te ontwikkelen die afhankelijkheden van andere repositories automatisch uitvoert voordat deze repository wordt gestart.

---

## 3.2 Uitbreiding van databronnen

Voor betere analyses en prognoses kan het project worden uitgebreid met aanvullende databronnen, zoals:

* **PortalPlus**
* **SIS (inschrijfdata)**

Daarnaast zou het waardevol zijn om:

* inschrijvingen per week uit het dezelfde periode van de voorgaande jaren te visualiseren.


---

## 3.3 Verbetering van visualisaties

In samenwerking met eindgebruikers kunnen de visualisaties verder worden ontwikkeld.

Mogelijke verbeteringen:

* uitbreiding van dashboards en grafieken
* toevoeging van aanvullende filters
* visualisatie van modelvalidatie

Een belangrijke uitbreiding kan het toevoegen van een **betrouwbaarheidsindex of onzekerheidsmarge bij voorspellingen** zijn.

---

## 3.4 Gebruik en toegankelijkheid

De huidige applicatie vereist relatief veel technische kennis om te gebruiken.

Om het gebruik binnen de organisatie te vergroten, zou het wenselijk zijn dat de Streamlit-applicatie **gehost kan worden binnen de organisatie**. Hierdoor kan de applicatie via een webinterface toegankelijk worden gemaakt voor eindgebruikers.

---

# 4. Technische uitdagingen

## Afhankelijkheid van andere repositories

De huidige repository is afhankelijk van twee andere repositories voor inputdata.

Dit betekent dat:

* eerst deze twee repositories uitgevoerd moeten worden;
* daarna pas deze repository kan worden gebruikt.

In de huidige situatie moeten dus drie repositories werkend zijn om de applicatie te kunnen draaien. Dit maakt implementatie en onderhoud complex.

Een mogelijke oplossing is:

* automatisering via pipelines
* centralisatie van data-output
* integratie van de verschillende repositories.

---

## Beschikbaarheid van CAMBO-data

CAMBO-data wordt momenteel slechts **één keer per jaar beschikbaar gesteld**, na afloop van het studiejaar.

Voor prognoses gedurende het studiejaar zou het wenselijk zijn dat deze data ook tussentijds beschikbaar is.

---

## Gebruiksvriendelijkheid

De huidige applicatie is voornamelijk gericht op technische gebruikers (bijvoorbeeld data-analisten).

Voor breder gebruik binnen de organisatie zijn mogelijk nodig:

* hosting van de applicatie
* automatisering van data-updates
* vereenvoudiging van de gebruikersinterface.

---

# 5. Organisatorische aandachtspunten

Voor verdere ontwikkeling van het project wordt aanbevolen om:

* een **key user groep** samen te stellen;
* relevante stakeholders te betrekken bij verdere ontwikkeling;
* verantwoordelijkheden voor beheer en onderhoud vast te leggen.


---

# KORTE VERSIE

# 📊 CAMBO Instroomanalyse en Prognose

Deze repository bevat een eerste prototype voor het analyseren van **CAMBO-data** en het genereren van **instroomprognoses**, inclusief een **Streamlit-visualisatie** van de resultaten.

## Projectonderdelen

Het project bestaat uit drie hoofdcomponenten:

1. **Data-analyse en preparatie**

   * opschonen en voorbereiden van CAMBO-data

2. **Prognosemodel**

   * genereren van instroomvoorspellingen

3. **Visualisatie**

   * interactieve weergave via een Streamlit-app

---

## Huidige beperkingen

* De repository is afhankelijk van **twee andere repositories** voor inputdata.
* CAMBO-data is momenteel **slechts één keer per jaar beschikbaar**.
* Het draaien van de applicatie vereist momenteel **relatief veel technische kennis**.

---

## Mogelijke verbeteringen

### Technisch

* Integratie van de drie onderdelen in één package.
* Ontwikkelen van pipelines voor data-invoer.
* Automatiseren van afhankelijkheden tussen repositories.

### Data

* Koppelen van inschrijvingen per week uit voorgaande jaren.
* Toevoegen van extra databronnen zoals:

  * PortalPlus
  * SIS

### Visualisaties

* Uitbreiding van dashboards.
* Toevoegen van modelvalidatie en betrouwbaarheidsindicatoren.

### Gebruik

* Hosten van de Streamlit-app binnen de organisatie.

---

## Organisatie

Voor verdere ontwikkeling wordt aanbevolen om:

* een **key user groep** samen te stellen
* relevante stakeholders te betrekken bij doorontwikkeling.

---
