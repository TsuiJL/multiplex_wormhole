#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 18:36:10 2024

@author: maggiehallerud
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title: TABULATE MFEprimer DIMERS
Created on Wed Aug  2 11:57:09 2023
@author: maggiehallerud

Dependencies: numpy (developed with version 1.26.2)

Purpose: Converts text output from MFEprimer dimer function into a pairwise interaction table
        and sum of primer interactions per primer and primer pair
"""

# load dependencies
import os
import sys
import csv
import gc
import numpy as np #version 1.26.2
from operator import truth # converts anything>=1 to True and =0 to False
#import itertools #paralellized filtering, etc.
#import multiprocessing



def main(ALL_DIMERS, END_DIMERS, OUTPATH, OUTPRIMERPATH=False):
    """
    ALL_DIMERS : Filepath
        Output from MFEprimer dimer
    END_DIMERS : Filepath
        Output from MFEprimer dimer -p
    OUTPATH : Filepath
        Filepath prefix for all primer pair outputs
    OUTPRIMERPATH : Filepath [DEFAULT: None]
        Filepath prefix for all primer outputs
    -------
    Converts MFEprimer dimer outputs into CSV tables
    """
    
    print("Reading in files............")
    # read in files - convert each interaction to a single line in array
    all_dimers = ReadDimerTXT(ALL_DIMERS)
    if END_DIMERS is None:
        end_dimers = []
    else:
        end_dimers = ReadDimerTXT(END_DIMERS)
    endpath = OUTPATH+'_endDimers.csv'
    allpath = OUTPATH+'_allDimers.csv'
    exportToCSV(end_dimers, endpath)    
    exportToCSV(all_dimers, allpath)
    
    print("Extracting non-end dimers............")
    # subset all dimers for all non-end dimers
    #middle_indx = list(filter(lambda x: all_dimers[x] not in end_dimers, range(len(all_dimers))))
    #middle_dimers = [all_dimers[x] for x in middle_indx]
    #middle_dimers = list(itertools.filterfalse(lambda x: x in end_dimers, all_dimers))
    #exportToCSV(middle_dimers, midpath)
    # grep options: -v inverse search -x selects lines that fully match -F interprets pattern 
    #as list of fixed strings (i.e., ignores special chars) -f searches for matches per line in given file
    midpath = OUTPATH+'_middleDimers.csv'
    # this unix command takes the difference between the 2 dimerfiles and only saves lines found in the all dimers file
    # it only works if both files are sorted
    endpath_sort = OUTPATH+'_endDimers_sorted.csv'
    allpath_sort = OUTPATH+'_allDimers_sorted.csv'
    os.system("sort "+endpath+" > "+endpath_sort)
    os.system("sort "+allpath+" > "+allpath_sort)
    os.system("diff "+endpath_sort+" "+allpath_sort+" | grep '^>' | sed 's/^>//g'  > "+midpath)
    
    print("Combining end dimers and non-end dimers.......")
    # combine middle and end dimers into same array
    #dimers = end_dimers + middle_dimers #too slow-stalls with large files!
    #dimers = np.concatenate((end_dimers, middle_dimers)) #somehow even slower!
    # If this step is a problem, could also write dimer lists to files and then 'paste' in bash
    # this unix binary command merges these two files
    dimerpath = OUTPATH+"_mergedDimers.csv"
    os.system("cat "+midpath+" "+endpath+" > "+dimerpath)
    # now we'll read in this file...
    dimers = ReadDimerCSV(dimerpath)
    
    print("Extracting primer ID info.....")
    # get list of primer IDs, locusIDs, and primer pair IDs
    with open(ALL_DIMERS, 'r') as file:
        lines = file.readlines()
        start_indx = list(filter(lambda x: 'Primer ID' in lines[x], range(len(lines))))[0]
        end_indx = list(filter(lambda x: 'Dimer List' in lines[x], range(len(lines))))[0]
        primerIDs = [lines[x].split(' ')[0] for x in range(start_indx+3, end_indx-4)]
        locusIDs = [primerIDs[x].split('_')[0]+'_'+primerIDs[x].split('_')[1] for x in range(len(primerIDs))]
        pairIDs = [locusIDs[x]+'_'+primerIDs[x].split('_')[2] for x in range(len(primerIDs))]
    #del lines # clean up
    gc.collect() # clean up
    
    print("Calculating pairwise primer pair interactions........")
    # aggregate the number of interactions per primer pair
    primer_pairs = list(set(pairIDs))
    pair_loci = [primer_pairs[x].split('_')[0]+'_'+primer_pairs[x].split('_')[1] for x in range(len(primer_pairs))]
    pair_interactions = tabulateDimers(dimers, primer_pairs, pair_loci, pairs=True)
    # convert to binary
    pair_interactions_bin = []
    pair_interactions_bin.append(pair_interactions[0])
    for j in range(1, len(pair_interactions), 1):
        rowid = pair_interactions[j][0]
        out = [rowid, *map((0).__add__, map(truth, pair_interactions[j][1:]))]
        pair_interactions_bin.append(out)
    
    print("Calculating total interactions per primer pair...........")
    # calculate sum of interactions for each primer pair
    pair_sums = totalDimers(pair_interactions) #total interactions
    pair_sums_bin = totalDimers(pair_interactions_bin) # total pairs interacted with
    
    print("Saving primer pair output files!")
    ## Export all files
    # export total pairwise interactions per primer pair (wide)
    pairwide = OUTPATH + '_wide.csv'
    exportToCSV(pair_interactions, pairwide)
    
    # export binary pairwise interactions per primer pair (wide)
    pairwidebin = OUTPATH + '_binary_wide.csv'
    exportToCSV(pair_interactions_bin, pairwidebin)
    
    # export total interactions per primer pair (long)
    pairlong = OUTPATH + '_sum.csv'
    exportToCSV(pair_sums, pairlong)

    # export total # pairwise interactions per primer pair long (long)
    pairlongbin = OUTPATH + '_binary_sum.csv'
    exportToCSV(pair_sums_bin, pairlongbin)
    
    # calculate interactions per primer
    if OUTPRIMERPATH!="False":
        print("")
        print("")
        print("Calculating pairwise primer interactions..........")
        # primers - total # interactions
        primer_interactions = tabulateDimers(dimers, primerIDs, locusIDs, pairs=False)
        # convert to binary
        primer_interactions_bin = []
        primer_interactions_bin.append(primer_interactions[0])
        for j in range(1, len(primer_interactions), 1):
            rowid = primer_interactions[j][0]
            out = [rowid, *map((0).__add__, map(truth, primer_interactions[j][1:]))]
            primer_interactions_bin.append(out)
    
        # calculate # interactions per primer
        print("Calculating total interactions per primer............")
        primer_sums = totalDimers(primer_interactions) # total interactions       
        primer_sums_bin = totalDimers(primer_interactions_bin) # total primers interacted with
        
        print("Saving primer output files!")
        # export total interactions per primer (long)
        primerlong = OUTPRIMERPATH + '_sum.csv'
        exportToCSV(primer_sums, primerlong)    
        # export pairwise interactions per primer (wide)
        primerwide = OUTPRIMERPATH + '_wide.csv'
        exportToCSV(primer_interactions, primerwide)
        # export # primers each primer interacts with (long)
        primerlong = OUTPRIMERPATH + '_binary_sum.csv'
        exportToCSV(primer_sums_bin, primerlong)    
        # export pairwise interactions per primer (wide)
        primerwide = OUTPRIMERPATH + '_binary_wide.csv'
        exportToCSV(primer_interactions_bin, primerwide)    



def ReadDimerTXT(infile):
    dimers = []
    with open(infile, 'r') as file:
        lines=file.readlines()
        dimer_indx = list(filter(lambda x: 'Dimer' in lines[x], range(len(lines))))[2:] # skip first two (headers)
        for i in dimer_indx:
            # grab all lines associated with this interaction & parse
            line1 = lines[i].strip().split(' ')
            line2 = lines[i+2].strip().split(' ')
            primer1 = line1[2]
            primer2 = line1[4]
            # we'll extract these later to reduce some memory reqs
            pair1 = primer1.replace('_FW','').replace('_REV','')
            pair2 = primer2.replace('_FW','').replace('_REV','')
            score = line2[1].replace(',','')
            delta_g = line2[5]
            #structure = lines[i+4:i+7] # no use for this yet
            dimers.append([primer1, primer2, pair1, pair2, score, delta_g])
    # convert to numpy array
    #array = np.asarray(dimers)
    return dimers
    gc.collect()#clean up



def ReadDimerCSV(infile):
    dimers = []
    with open(infile, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            primer1 = row[0].strip()
            primer2 = row[1].strip()
            pair1 = row[2].strip()
            pair2 = row[3].strip()
            score = row[4].strip()
            deltaG = row[5].strip()
            newrow = [primer1, primer2, pair1, pair2, score, deltaG]
            dimers.append(newrow)
    dimers = np.array(dimers)
    return dimers
    gc.collect()
    


def tabulateByRow(i, primer_ids, locus_ids, dimers, pairs):
    # progress tracking
    #if(i%10 == 0):
    #    print('     ' + str(int(i/len(primer_ids)*100)) + '% primers finished')
    print("......Tabulating dimers for "+str(i))
    # set up empty arrays to hold results
    interactions_row = []
    # add rowname as first value in array
    rowID = primer_ids[i]
    interactions_row.append(rowID)
    # loop through every other primer pair to find dimers- these will be the 'columns'
    for j in range(len(primer_ids)):
        # grab primer ID
        colID = primer_ids[j]
        print(".............................."+str(j))
        # if these primers are for the same locus, then set to 0 because
        # we already filtered for homodimers and pair dimers, and dimers 
        # between pairs for the same locus don't matter because there will 
        # only ever be one primer pair per locus in a set
        if locus_ids[i]==locus_ids[j]:
            interactions_row.append(0)
        else:
            # for pairs, look at fields 3-4 in dimer array
            if pairs:
                # get all dimers for these primers (including both pairwise comparisons)
                #high_ratio_company = combined_data[(combined_data[:, 0] > 500) & (combined_data[:, 1] < 30)]
                sub1_dimer_indx = dimers[((dimers[:,2]==rowID) & (dimers[:,3]==colID))]
                sub2_dimer_indx = dimers[((dimers[:,3]==rowID) & (dimers[:,3]==colID))]
                #sub1_dimer_indx = list(filter(lambda x: dimers[x][2]==rowID and dimers[x][3]==colID, range(len(dimers))))
                #sub2_dimer_indx = list(filter(lambda x: dimers[x][2]==rowID and dimers[x][3]==colID, range(len(dimers))))
            # for primers, look at fields 1-2 in dimer array
            else:
                sub1_dimer_indx = list(filter(lambda x: dimers[x][0]==rowID and dimers[x][1]==colID, range(len(dimers))))
                sub2_dimer_indx = list(filter(lambda x: dimers[x][0]==rowID and dimers[x][1]==colID, range(len(dimers))))
            # grab the # of primer interactions for this comparison
            Ndimers = len(sub1_dimer_indx)+len(sub2_dimer_indx)
            # add to row
            interactions_row.append(Ndimers)
    # return populated row
    return interactions_row



def tabulateDimers(dimers, primerIDs, locusIDs, pairs):
    # tabulate dimers per primer interaction row-by-row using simple list comprehension
    results = [tabulateByRow(x, primerIDs, locusIDs, dimers, pairs) for x in range(len(primerIDs))]
    # set up array to hold results
    header = ['ID']
    header[1:len(primerIDs)+1] = primerIDs
    pairwise_interactions = [header]
    # copy results into array
    pairwise_interactions[1:len(pairwise_interactions)+1] = results
    return pairwise_interactions
    #return [pool.apply(tabulateByRow, args=(x, primerIDs, locusIDs, dimers, pairs)) for x in range(len(primerIDs))]



def totalDimers(pairwise_interactions):
    sums = []
    for row in range(1, len(pairwise_interactions)):
        rowid = pairwise_interactions[row][0]
        ndimers = sum(pairwise_interactions[row][1:])
        sums.append([rowid, ndimers])
    return sums



def exportToCSV(inArray, outCSV):
    with open(outCSV, 'w') as file:
        for line in inArray:
            str_line = str(line)[1:-1].replace("'", "")
            file.write(str_line+"\n")



if __name__ == "__main__":
   main(sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        str(sys.argv[4]))
    # set up pool specs for multiprocessing
   # with multiprocessing.Pool(4) as pool:
   #     print(Pooling.tabulateDimers)