#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__description__ = "get infos from postgres database (crossref data) in order to compare them with KE data" \
                  "the aim is to retireve DOI from crossref missing in KE data"
__author__ = "Eva Seidlmayer <eva.seidlmayer@gmx.net>"
__copyright__ = "2021 by Eva Seidlmayer"
__license__ = "ISC license"
__email__ = "seidlmayer@zbmed.de"
__version__ = "1 "


#import psycopg2
#import kinakuta_hidden
import elysium_hidden
import pandas as pd
import regex as re
import argparse
import csv
from psycopg2 import connect
from tqdm import tqdm


# Load the secrets
#secrets = kinakuta_hidden.secrets()
secrets = elysium_hidden.secrets()
#conn = psycopg2.connect(host=secrets['host'],
 #                       port=secrets['port'],
  #                      database=secrets['database'],
   #                     user=secrets['user'],
    #                    password=secrets['pass'],
     #                   connect_timeout=3,
      #                  keepalives=1,
       #                 keepalives_idle=30,
        #                keepalives_interval=10,
         #               keepalives_count=5
          #              )
config = {
    "host" : secrets['host'],
    "dbname" : secrets['database'],
    "user" : secrets['user'],
    "password" : secrets['pass'],
    "port" : secrets['port']
}

# define cursor
#cur = conn.cursor('elysium')
#cur.itersize = 10000



def main():
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('input_file_csv')
    parser.add_argument('output_file_csv')
    args = parser.parse_args()

    # set-up output file
    with open(args.output_file_csv, 'a') as csvfile:
        csv_writer = csv.writer(csvfile)

        # for evaluation file
        #csv_writer.writerow(['dbrecordid', 'doi_KE', 'doi_crossref', 'sortyear_KE','publyear_KE', 'published_print_crf',\
        #                     'publishd_online_crf', 'authors_KE',  'authors_crossref'])

        # for productiv harvesting
        csv_writer.writerow(
            ['dbrecordid',  'doi_crossref', 'sortyear_KE', 'publyear_KE', 'published_print_crf', \
             'publishd_online_crf', 'authors_KE', 'authors_crossref'])

        # load KE data
        # replace ' by U+0027 unicode
        # remove . at the end of title

        # for evaluation file
        #col_list = ['dbrecordid','doi_ke','authors','sortyear','publyear', 'title']

        # for productive harvesting
        col_list = ['dbrecordid', 'authors', 'sortyear', 'publyear', 'title']
        input = pd.read_csv(args.input_file_csv, usecols=col_list, low_memory=False)
        input = input.drop_duplicates()

        with connect(**config) as conn:
            for index, row in tqdm(input.iterrows()):
                if row['title']:

                    # trim title, replace ' and remove . at the end of title
                    try:
                        if "'" in row['title']:
                            tit = re.sub(r"'", "U+0027", row['title'])
                        else:
                            tit = row['title']
                    except:
                        continue
                    if tit[-1] == '.':
                        tit = tit[:-1]
                    else:
                        continue

                    # define SQL comand
                    sql = f'''SELECT * FROM crossref_expand_data WHERE title LIKE '%{tit}%'; '''

                    # psycopg2 connection to database
                    #with connect(**config) as conn:
                    with conn.cursor("titel_curser") as cur:
                        cur.itersize = 1000

                        # execute SQL comand
                        cur.execute(sql)

                        # load results in variable
                        result = cur.fetchall()
                        for res_row in result:
                            # for evaluation file
                            # infos = row['dbrecordid'], row['doi_ke'], res_row[2], row['sortyear'], row['publyear'], \
                            #        res_row[3], res_row[4], row['authors'], res_row[5]
                            authors_crossref = [res_row[5], res_row[6]]

                            # for productive harvesting
                            infos = row['dbrecordid'],  res_row[2], row['sortyear'], row['publyear'], \
                                    res_row[3], res_row[4], row['authors'], authors_crossref
                            csv_writer.writerow(infos)
                else:
                    continue


    print('done')
main()








