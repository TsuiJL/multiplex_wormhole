# set up env
library(openPrimeR)
library(vcfR)
library(stringr)


#### READ IN SEQUENCES
setwd('/Users/maggiehallerud/Desktop/Marten_Fisher_Population_Genomics_Results/Marten/SNPPanel/Panel2_200initialpairs/')
# load template sequences
marten_seq <- read_templates('CoastalMartenMAF10.MAMA.trimmed.fa') #input fasta file
#View(as.data.frame(marten_seq$Sequence))

# load VCF
marten_vcf <- read.vcfR('CoastalMartens.maf10.Mar2024.recode.vcf')
marten_fix <- as.data.frame(marten_vcf@fix) #this file holds SNP positions 
#names(marten_fix) <- c("CHROM","POS","ID","MAJOR","MINOR","UNK","UNK","ALLELE_FREQ")

# fix locus IDs
marten_fix$CHROM <- unlist(lapply(marten_fix$ID, function(X) strsplit(X,':')[[1]][1]))

# reset allowed primer binding locations- check VCF for position of SNPs on each sequence
# go through one at a time & fix...
for (i in 1:nrow(marten_seq)){
  id <- str_split(marten_seq$ID[i], '>')[[1]][2]
  snps <- marten_fix$POS[marten_fix$CHROM==as.numeric(id)]
  snps <- as.numeric(snps)
  min_snp <- min(snps)
  max_snp <- max(snps)
  if (min_snp==Inf) min_snp <- marten_seq$Sequence_Length[i]
  if (max_snp==-Inf) max_snp <- 1
  marten_seq$Allowed_End_fw[i] <- min_snp-1
  marten_seq$Allowed_Start_rev[i] <- max_snp+1
  marten_seq$Allowed_End_rev[i] <- marten_seq$Sequence_Length[i]
}#for i

# check all are populated
marten_seq$Allowed_Start_fw
marten_seq$Allowed_End_fw
marten_seq$Allowed_Start_rev
marten_seq$Allowed_End_rev
#marten_seq$Allowed_Start_fw <- 1

# adjust allowed binding regions
for (i in 1:nrow(marten_seq)){
  marten_seq$Allowed_fw[i] <- substr(marten_seq$Sequence[i], marten_seq$Allowed_Start_fw[i], marten_seq$Allowed_End_fw[i])
  marten_seq$Allowed_rev[i] <- substr(marten_seq$Sequence[i], marten_seq$Allowed_Start_rev[i], marten_seq$Allowed_End_rev[i])
}#for i

# check allowed binding regions
head(marten_seq$Allowed_fw)
head(marten_seq$Allowed_rev)

# double check that microhaps are properly represented
counts=data.frame(table(marten_fix$CHROM))
microhaps=counts[counts$Freq>1,]
marten_fix[marten_fix$CHROM==microhaps$Var1[2],]
marten_seq[marten_seq$ID==">10057",]

# export microhaplotypes
nrow(microhaps)
microhaps$Var1 <- paste0('>', microhaps$Var1)
microhaps <- microhaps[order(microhaps$Freq),]
microhaps_seq <- marten_seq[which(marten_seq$ID %in% microhaps$Var1)]
nrow(microhaps_seq)
#microhaps_seq <- microhaps_seq[which(nchar(microhaps_seq$Allowed_rev)>=18 | nchar(microhap_seq$Allowed_fw)>=18),]
#write.csv(microhaps_seq$ID, 'MartenTemplates_MAF30-repBaseFilter_01Aug2023_microhaplotypes.csv', row.names=FALSE)

# remove any loci with more than 3 loci (these are likely untrustworthy in our case...)
sum(microhaps$Freq>3)#these might not be trustworthy (paralogs)....
microhaps_loci <- microhaps$Var1[microhaps$Freq>3]
marten_seq <- marten_seq[!marten_seq$ID %in% microhaps_loci,]

# remove any that don't have enough binding space
marten_seq <- marten_seq[which(nchar(marten_seq$Allowed_fw)>=18 & nchar(marten_seq$Allowed_rev)>=18),]
nrow(marten_seq)

# check that there's only one line per locus
nrow(marten_seq)
length(unique(marten_seq$Header))

## check correlations between loci
# extract genotypes
gt <- extract.gt(marten_vcf, element="GT")
for (i in 1:nrow(gt)){
  gt[i,gt[i,]=="0/0"] <- 0
  gt[i,gt[i,]=="0/1"] <- 1
  gt[i,gt[i,]=="1/1"] <- 2
}#for
gt <- as.data.frame(gt)
gt <- apply(gt, MARGIN=1, function(X) {as.numeric(X)})

# calc correlations, sum high correlations per SNP
cors <- cor(gt, use="pairwise.complete")
cors <- as.data.frame(cors)
high_cors <- apply(cors, MARGIN=1, function(X) as.numeric(X>0.6))
#sum(high_cors,na.rm=T)-nrow(high_cors)
totalcorrs <- rowSums(high_cors, na.rm=T)

# grab loci IDs w/ > 400 high corrs (correlated with ~10% of SNPs)
sum(totalcorrs>400)
highcorIDs <- rownames(cors)[totalcorrs>400]
highcor_loci <- unlist(lapply(highcorIDs, function(X){ strsplit(X, ":")[[1]][1]}))

for (l in highcor_loci){
  l <- paste0(">",l)
  marten_seq <- marten_seq[which(marten_seq$ID!=l),]
}#for


# double check that everything looks OK...
View(marten_seq)

# export IDs, templates, targets as CSV for use with primer3
target_start <- marten_seq$Allowed_End_fw+1 #additional 1 is simpy for length calculations!
target_end <- marten_seq$Allowed_Start_rev
target_len <- target_end - target_start
targets <- paste0(as.character(target_start), ",", as.character(target_len))
marten_csv <- data.frame(SEQUENCE_ID=str_replace_all(marten_seq$ID,'>',''),
                         SEQUENCE_TEMPLATE=marten_seq$Sequence,
                         SEQUENCE_TARGET=targets)
write.csv(marten_csv, 'CoastalMartenTemplates_MAF10_CENSOR_Martesmartes_trimmed.csv', row.names=FALSE)                         

