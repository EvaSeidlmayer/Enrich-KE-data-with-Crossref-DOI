# Enrich-KE-data-with-Crossref-DOI
Enrichment of ZB MED Knowledge Environment data with Crossref DOI

task: enrichment of KE data with crossref DOI
goal: deduplication of KE data by DOI

# download current dump of ZB MED KE database
 mongoexport --host="10.0.4.174" --db=livivo --collection=livivodata --out=zbmedke_20211029.json

# set up of crossref database
1. download crossref: 112+ Million records https://academictorrents.com/details/e4287cb7619999709f6e9db5c359dda17e93d515
2. set up postgres data base; we have it on VM Kinakuta and on VM Elysium
how to: see Klaus' Git repositorium:
https://gitlab.zbmed.de/klaus.lippert/datasource/

3. create sub table
```
postgres=# CREATE TABLE  crossref_data (id serial, title varchar, doi varchar, authors_given varchar, authors_family varchar);
``` 

4. create index 
```
INSERT INTO public.crossref_data (title, doi, published_print, published_online, authors_given, authors_family) SELECT (data->'title')::text, (data->'DOI')::text, (data->'published-print'->'date-parts'->0->0)::text, (data->'published-online'->'date-parts'->0->0)::text, (data->'author'->0->'given')::text,  (data->'author'->0->'family')::text FROM crossref.raw; 
```

# Productive work
1. Harvesting of titles from KE for single sortyears
python3 harvest_KE_for-no-doi.py zbmedke_20211029.json --filter-year years-for-harvesting.txt -o 2018
years-for-harvesting.txt containes in this case "2018"

result:
```
dbrecordid,identifier,authors,title,sortyear,publyear,publisher
565896,,"['Edelstein, Emma']",Asclepius,2018,,['Johns Hopkins Press']
BASE::ftagecon:oai:ageconsearch.umn.edu:252967,,"['Wang, Youzhi', 'Delgado, Michael S.', 'Marshall, Maria I.', 'Dobbins, Craig L.']",Generational Shadow in Farming Business,2018,2018,
```

2. Harvesting crossref 
python3 crossref-sql.py metadata_KE_2018.csv  metadata_KE-crf_2018.csv  

the program uses the SQL query to query the postgres database. the title (string) is compared to the title in the database
```
f''' SELECT * FROM crossref_expand_data WHERE title LIKE '%{tit}%'; '''
SELECT *FROM crossref_data WHERE title LIKE '%Predicting individual differences in conflict detection and bias susceptibility during reasoning%'; 
```
result:
```
dbrecordid,doi_crossref,sortyear_KE,publyear_KE,published_print_crf,publishd_online_crf,authors_KE,authors_crossref
M26698838,"""10.1016/j.ejogrb.2012.07.030""",2016.0,2016,2012,,"['Puchar, Anne', 'Feyeux, Cécile', 'Luton, Dominique', 'Koskas, Martin']","['""Henri""', '""Marret""']
M29019353,"""10.24875/aidsrev.m17000009""",2019.0,2019,2017,2017,"['Yendewa, George A', 'Salata, Robert A']","['""George""', '""A. Yendewa""']"
``` 
It is important to filter out all dbrecordid which occur more than once. Double (and more) occurence is a strong indicator 
that  dbrecordid refers not to a scientific article but to some "letter to the editor", "Editorial" thing, or similar.
We tried exclude those items beforehand by filtering for "DOCTYPE" "scientific article" in KE in the first place. 
However, removing all double dbrecordid is recommended due to noisy KE-data. 



# Evaluation
1. Harvesting of titles from KE for single sortyears
python3 harvest_KE_for deduplication.py zbmedke_20211029.json --filter-year years-for-harvesting.txt -0 KE_2018-for-deduplication
result:
```
dbrecordid,doi_ke,identifier,authors,title,sortyear,publyear,publisher
M28220487,10.1111/1365-2656.12658,,"['Shaw, Allison K', 'Kokko, Hanna', 'Neubert, Michael G']",Sex difference and Allee effects shape the dynamics of sex-structured invasions.,2018,2018,
M28240356,10.1111/1365-2656.12662,,"['Berec, Luděk', 'Kramer, Andrew M', 'Bernhauerová, Veronika', 'Drake, John M']",Density-dependent selection on mate search and evolution of Allee effects.,2018,2018,
```
2. Harvesting crossref 
python3 crossref-sql.py metadata_KE_2018.csv  metadata_KE-crf_2018.csv
result:
```
dbrecordid,doi_KE,doi_crossref,sortyear_KE,published_print_crf,publishd_online_crf,title
M28372536,10.1177/1933719117699706,"""10.1177/1933719117699706""",2018,2018,2017,HoxA10 and HoxA11 Regulate the Expression of Contraction-Associated Proteins and Contribute to Regionalized Myometrium Phenotypes in Women
M28372829,10.1016/j.socscimed.2017.03.058,"""10.1016/j.socscimed.2017.03.058""",2018,2018,,The weight of racism: Vigilance and racial inequalities in weight-related measures
```

3. comparison of DOI from KE and retrieved DOI from crossref database 
python3 harvesting_crossref_evaluation.py
The input is hard coded. 
since single DOI/title/dbrecordid refers to journals, one title returns very many entries with very many DOI. 
In order to avoid this, having one dbrecordid with dozens of crossref DOI, we excluded row with dbrecordids which appeared more than once from the results.
It was noticed that DOI hab been writen with capital letters and sometimes with lower cases. To avoid any inconsitencies due to upper oder lower case, all DOIs turned to lowercase. 
We than set the condition of the same publication year. 
based on these conditions we compared the DOIs from KE with those retrieved from Crossref:
result:

" 21849 titles are in the file
number same print years 19322
number of unequal print years 2527
of those who have same years 19197 have same DOIs, this is 0.99353069040472 percentage
of those who have same years 125 have not same DOIS, this is  0.0064693095952799914 percentage "
