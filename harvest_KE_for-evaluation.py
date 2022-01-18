#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: extract_jsonl
Author: Lukas Galke, Eva Seidlmayer
Email: seidlmayer@zbmed.de
Github:
Description: metadata (Extract DOI, authors, titles from ZBMEDKE), filtering option for publication year
Last Change: Sep 5, 2021
"""

import argparse
import os
import jsonlines
import re
import pandas as pd
from tqdm import tqdm

DEBUG = False


def main():
    """ Extracts separate tables from jsonlines file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl_file")
    parser.add_argument("-o", "--output", dest='save', default=None, type=str,
                        help="Save files in this directory")
    parser.add_argument("--normalize", default=False, action='store_true',
                        help="Normalize string columns")
    parser.add_argument("--filter-year", default=None, nargs='*',
                        help="Extract only documents, which are publicated in the specified year(s) given in file (one per line).")
    args = parser.parse_args()


    #filter for publication year
    if args.filter_year is not None:
        print('Loading filter publication year(s)')
        year_filter = []
        for fpath in args.filter_year:
            with open(fpath, 'r') as fhandle:
                for line in fhandle:
                    year_filter.append(line.strip())
        print("Filtering for", len(year_filter), "sort year(s)")
        print("Filtering for", year_filter, "as sort year(s)")
    else:
        year_filter = None

    #open ZB MED KE data file
    with jsonlines.open(args.jsonl_file) as json:
        flat_gen = ((d['_id']['$oid'], d['liv']['orig_data'])
                    for d in json)


        #set counter
        n_extracted = 0

        # initiate metadata container
        metadata = []

        for identifier, data in tqdm(flat_gen):
            if "sortyear" not in data:
                # publication year not specified, drop record
                continue
            if data["sortyear"][0] not in year_filter:
                continue
            if "DOI" not in data:
                # publication has already a DOI, drop record
                continue
            try:
                if data["DOCTYPE"][0] != 'ARTIKEL':
                    continue
            except:
                continue

            #initiate author container
            authors = []

            #define infos: DOI, oid, authors, title, publyear

            dbrecordid = data.get('DBRECORDID') if 'DBRECORDID' in data else None
            doi = data.get('DOI')[0] if 'DOI' in data else None
            try:
                for term in data['AUTHOR']:
                    authors.append(term)
            except: continue
            tit = data.get('TITLE') if 'TITLE' in data else None
            publyear = data.get('PUBLYEAR') if 'PUBLYEAR' in data else None
            sortyear = data.get('sortyear') if 'sortyear' in data else None
            publisher = data.get('PUBLISHER') if 'PUBLISHER' in data else None
            otherID = data.get('IDENTIFIER') if 'IDENTIFIER' in data else None


            try:
                title = "".join(map(str, tit))
            except: Exception
            try:
                publyear = "".join(map(str, publyear))
            except: Exception
            try:
                sortyear = "".join(map(str, sortyear))
            except: Exception
            sortyear = int(sortyear)
            metadata.append((dbrecordid, doi, otherID, authors, title, sortyear, publyear, publisher))


            # add 1 to counter
            n_extracted += 1


    print("Extracted %d papers" % n_extracted)

    # create dataframes from infos
    df_paper_metadata = pd.DataFrame(metadata,
                                     columns=['dbrecordid',
                                              'doi_ke',
                                              'identifier',
                                              'authors',
                                              'title',
                                              'sortyear',
                                              'publyear',
                                              'publisher'])


    dfs = [
        # dataframe name, dataframe, whether to save index
        ('metadata_KE', df_paper_metadata, False)
    ]

    if args.save is not None:
        # Dumps everything to disk
        os.makedirs(args.save, exist_ok=True)
        for fname, dframe, save_index in dfs:
            dframe.to_csv(os.path.join(args.save, fname + '.csv'),
                          index=save_index)
        with open(os.path.join(args.save, 'args.txt'), 'w') as fh:
            print(args, file=fh)


if __name__ == "__main__":
    main()