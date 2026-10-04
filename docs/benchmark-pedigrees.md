# Candidate benchmark pedigrees

A survey of pedigrees that pedsum could be run on and compared against
published statistics. Compiled 2026-10-03.

## How the citations were checked

The survey was compiled in a cloud sandbox that blocked doi.org, Crossref,
PubMed, Europe PMC, OpenAlex, Dryad and publisher pages. On 2026-10-04 every
DOI was re-checked against its Crossref record (DataCite for Dryad and
Figshare), and each one resolves at doi.org. Entries without a DOI were
matched by title through Crossref or PubMed. A field still marked
`TODO: verify <field>` could not be confirmed from any live source.

"Status" columns:

- **fetched**: the file was downloaded and parsed.
- **listed**: the deposit was found but not downloaded. Dryad file downloads
  need an API token (see `benchmarks/published/dryad.py`).
- **blocked**: the host was unreachable; not checked.
- **restricted**: the data are not publicly downloadable.
- **fetched, no pedigree** and **genotypes only**: downloaded, but the
  deposit has no parent table to rebuild the pedigree from.
- **in the harness**: checked by `benchmarks/published/run_published.py`.

Numbers marked *recomputed* were reproduced from the downloaded file with a
throwaway script (not pedsum). Others come from the source as quoted.

---

## 1. Exact numeric targets (downloadable; published values recomputed)

### 1.1 purgeR zoo studbooks: `atlas`, `dama`, `arrui`, `dorcas`, `darwin`

- **Data:** R package purgeR 1.8.3, `data(atlas)` etc.
  https://github.com/cran/purgeR (`data/*.rda`). GPL-2. Status: fetched.
- **Size:** atlas 948 (*Gazella cuvieri*), dama 1,316 (*Nanger dama*),
  arrui 380 (*Ammotragus lervia*), dorcas 1,279 (*Gazella dorcas*),
  darwin 63 (Darwin/Wedgwood family).
- **Published values:**
  - Heredity abstract: Ne = 14, 11, 4 and 39 from individual ΔF over
    `target == 1`. Recomputed as 14.01041, 11.09927, 3.83865 and 39.32125.
  - atlas package tests: total F 197.2809, max F 0.4277344, equivalent
    complete generations summing to 5500.627, individual-ΔF Ne 8.184803
    (all rows) and 14.01041 (target).
  - Vignette `pop_Nancestors`: founder equivalents Nfe
    1.769424 / 3.583086 / 13.386468 / 2.614750 (arrui / atlas / dorcas /
    dama). The first, second and fourth were recomputed.
  - darwin: F = 0.06298828 for William Erasmus Darwin.
- **Citations:**
  - López-Cortegano E, Moreno E, García-Dorado A (2021). Genetic purging in
    captive endangered ungulates with extremely low effective population
    sizes. *Heredity* 127(5):433–442. https://doi.org/10.1038/s41437-021-00473-2
  - López-Cortegano E (2022). purgeR: inbreeding and purging in pedigreed
    populations. *Bioinformatics* 38(2):564–565.
    https://doi.org/10.1093/bioinformatics/btab599

### 1.2 GENLIB `genea140` (Quebec, extract of the BALSAC register)

- **Data:** R package GENLIB, `data(genea140)`.
  https://raw.githubusercontent.com/cran/GENLIB/master/data/genea140.rda
  (`ind, father, mother, sex`; 0 = unknown parent). GPL. Status: fetched.
- **Size:** 41,523 individuals, 140 probands.
- **Published values, all recomputed:**
  - 20,773 males and 20,750 females.
  - 7,399 founders.
  - 21,230 nuclear families.
  - 5,994 full sibships, the largest of size 14.
  - 18 generations.
  - Mean genealogical depth 9.4.
- **Citations:**
  - Gauvin H, Lefebvre J-F, Moreau C, Lavoie E-M, Labuda D, Vézina H,
    Roy-Gagnon M-H (2015). GENLIB: an R package for the analysis of
    genealogical data. *BMC Bioinformatics* 16:160.
    https://doi.org/10.1186/s12859-015-0581-5
  - Roy-Gagnon M-H, Moreau C, Bherer C, St-Onge P, Sinnett D, Laprise C,
    Vézina H, Labuda D (2011). Genomic and genealogical investigation of the
    French Canadian founder population structure. *Hum Genet*
    129(5):521–531. https://doi.org/10.1007/s00439-010-0945-x

### 1.3 visPedigree `deep_ped`

- **Data:** R package visPedigree 1.10.1, `data(deep_ped)`.
  https://github.com/cran/visPedigree. GPL-3. Status: fetched.
- **Size:** 4,396 rows; 4,399 individuals once missing parents are added.
- **Published values** (package vignette; the package's own output, not peer
  reviewed):
  - N 4,399, 483 sires, 554 dams, 138 founders, 13 generations. N and the
    sire and dam counts were recomputed.
  - fe 64.73344 and fa 44.12033.
  - Mean coancestry 0.0260693.
  - NeInbreeding 98.00425.
- **Citation:** Luan S, Kong J, Xia Z, Kang Z, Qiang G, Luo K, Sui J (2026).
  visPedigree: a comprehensive R package for tidying, analyzing, and
  visualizing breeding pedigrees. *Bioinformatics Advances* 6(1):vbag210.
  https://doi.org/10.1093/bioadv/vbag210

### 1.4 optiSel `PedigWithErrors` / `Phen` (Hinterwald cattle)

- **Data:** R package optiSel 2.1.0. https://github.com/cran/optiSel. GPL-2.
  Status: fetched.
- **Size:** 10,863 rows; 178 candidates in `Phen`. The file contains
  deliberate errors that optiSel's `prePed()` repairs.
- **Published values** (vignette `ped-vignette.html`):
  - Mean F of the `Phen` animals 0.01943394.
  - Coancestry Ne 97.95922.
  - Per-animal equiGen, fullGen, maxGen, PCI and F for 6 named IDs.
- **Citation:** Wellmann R (2019). Optimum contribution selection for animal
  breeding and conservation: the R package optiSel. *BMC Bioinformatics*
  20:25. https://doi.org/10.1186/s12859-018-2450-5

### 1.5 Small fixtures

| Pedigree | Data | Published value | Citation |
|---|---|---|---|
| Mrode example | `nadiv::Mrode2`; `AGHmatrix::ped.mrode`; the pedigreemm `?getA` example. Status: fetched. | F = 0.125 for animals 5 and 6; textbook A matrix | Mrode RA (2005). *Linear Models for the Prediction of Animal Breeding Values*, 2nd ed. CABI Publishing (TODO: verify place; Crossref gives UK, the Library of Congress record Cambridge, MA). ISBN 0-85199-000-2. https://doi.org/10.1079/9780851990002.0000 · Wolak ME (2012). nadiv: an R package to create relatedness matrices for estimating non-additive genetic variances in animal models. *Methods Ecol Evol* 3(5):792–796. https://doi.org/10.1111/j.2041-210X.2012.00213.x |
| Lacy (1989) example | `nprcgenekeepr::lacy1989Ped`; 7 rows in `tests/testthat/test_calcFE.R`. Status: fetched. | fe = 2.91 (package test 2.9090909) | Lacy RC (1989). Analysis of founder representation in pedigrees: founder equivalents and founder genome equivalents. *Zoo Biol* 8(2):111–123. https://doi.org/10.1002/zoo.1430080203 |
| Boichard toy pedigrees | `PyPedal/tests/boichard/boichard2{,a,b}.ped` in the PyPedal 2.0.3 tarball on SourceForge; PyPedal's tests (`pyp_tests.py`) assert the fe and fa below. Status: fetched; in the harness. | Table II, p. 12 (total / family 1 / family 2): founders 6 / 4 / 2, fe 5.6 / 4.0 / 2.0, fa 2.94 / 2.0 / 2.0, Ng 2.5 / 1.8 / 1.1. Reference population: the circled last generation of fig. 2. | Boichard D, Maignel L, Verrier E (1997). The value of using probabilities of gene origin to measure genetic variability in a population. *Genet Sel Evol* 29(1):5–23. https://doi.org/10.1186/1297-9686-29-1-5 |
| MCMCglmm `BTped` (blue tit) | `data(BTped)`, 1,040 rows. Status: fetched. | 212 founders, 106 full-sib families, all F = 0 (by construction) | Hadfield JD, Nutall A, Osorio D, Owens IPF (2007). Testing the phenotypic gambit: phenotypic, genetic and environmental correlations of colour. *J Evol Biol* 20(2):549–557. https://doi.org/10.1111/j.1420-9101.2006.01262.x · Hadfield JD (2010). MCMC methods for multi-response generalized linear mixed models: the MCMCglmm R package. *J Stat Softw* 33(2):1–22. https://doi.org/10.18637/jss.v033.i02 |
| nprcgenekeepr unit tests | `tests/testthat/`. Status: fetched. | Ne by sex ratio 6 / 3.6 / 2; Ne by variance 1.875 / 2.5; fg = 32/21 | nprcgenekeepr (CRAN package, v2.0.0), Raboin M, Therneau T, Vinson A, Sharp RM, Schultz M. *Genetic Tools for Colony Management*. 2026. No paper. |
| visPedigree `small_ped`, `inbred_ped` | In the package. Status: fetched. | fe 6.585209 and fa 2.666667; mean F by generation 0, 0, 0.25, 0.25, 0.4375 | As 1.3 |

---

## 2. Approximate or partial targets (downloadable)

### 2.1 Human and historical

| Pedigree | Data, status | N | Comparable values | Citation |
|---|---|---|---|---|
| Spanish Habsburgs | No published data file. Stand-in GEDCOM: https://raw.githubusercontent.com/jlmborges/VisAC/main/R_package/Charles_II_2022_04.ged (MIT). Status: fetched. | 198 (stand-in) | Published F: Philip I 0.025, Charles I 0.037, Philip II 0.123, Philip III 0.218, Philip IV 0.115, Charles II 0.254. Don Carlos 0.211 is TODO: verify. The stand-in gives lower values (Charles II 0.238) because it is shallower. | Alvarez G, Ceballos FC, Quinteiro C (2009). The role of inbreeding in the extinction of a European royal dynasty. *PLoS ONE* 4(4):e5174. https://doi.org/10.1371/journal.pone.0005174 · Ceballos FC, Álvarez G (2013). Royal dynasties as human inbreeding laboratories: the Habsburgs. *Heredity* 111(2):114–121. https://doi.org/10.1038/hdy.2013.25 |
| Darwin–Wedgwood | `purgeR::darwin` (1.1). GEDCOM stand-in: https://raw.githubusercontent.com/samoilev/swarm/main/Examples/darwin-wedgwood/darwin-wedgwood.ged (40 individuals; gives 0.0625 because the deeper link is missing). Status: fetched. | 63 | Darwin's children F = 0.0630 | Berra TM, Alvarez G, Ceballos FC (2010). Was the Darwin/Wedgwood dynasty adversely affected by consanguinity? *BioScience* 60(5):376–383. https://doi.org/10.1525/bio.2010.60.5.7 |
| royal92.ged (European royalty, Denis R. Reid 1992) | https://raw.githubusercontent.com/R-Computing-Lab/BGmisc/main/data-raw/royal92.ged, and as CSV: `.../royal92.csv`. Status: fetched. | 3,010 | No published pedigree statistics; use as a regression baseline. Recomputed: 992 founders, mean F 0.0022, max F 0.1875. | No pedigree-statistics paper. Used as one network in: Boyd ZM, Callor N, Gledhill T, Jenkins A, Snellman R, Webb B, Wonnacott R (2023). The persistent homology of genealogical networks. *Applied Network Science* 8:15. https://doi.org/10.1007/s41109-023-00538-7 |
| kinship2 `minnbreast` (Minnesota breast cancer families) | https://raw.githubusercontent.com/cran/kinship2/master/data/minnbreast.rda, plus `sample.ped.tab.gz` (55 rows). Status: fetched. | 28,081 | Package docs: 426 families. The paper describes 544 families, which does not match the packaged subset, so there is no reproduction target. | Sinnwell JP, Therneau TM, Schaid DJ (2014). The kinship2 R package for pedigree data. *Hum Hered* 78(2):91–93. https://doi.org/10.1159/000363105 · Sellers TA, Anderson VE, Potter JD, Bartow SA, Chen PL, Everson L, King RA, Kuni CC, Kushi LH, McGovern PG, Rich SS, Whitbeck J, Wiesner G (1995). Epidemiologic and genetic follow-up study of 544 Minnesota breast cancer families: design and methods. *Genet Epidemiol* 12(4):417–429. https://doi.org/10.1002/gepi.1370120409 |
| Ptolemaic dynasty | https://raw.githubusercontent.com/D-Jeffrey/gedcom-samples/main/famous%20family%20trees/royalty/Ptolemaic+Dynasty.ged (MIT). Status: fetched. | 38 | No published F. Extreme-inbreeding stress test only (recomputed: Ptolemy XII F = 0.426). | None. |
| GENLIB `geneaJi` / ribd `jicaque` (Jicaque, Honduras) | https://raw.githubusercontent.com/cran/GENLIB/master/data/geneaJi.rda. Status: fetched. | 29 (GENLIB) / 22 (ribd) | Described as a "modified version" of the original, so published values are not expected to match. | Chapman AM, Jacquard A (1971). Un isolat d'Amérique Centrale: les Indiens Jicaques de Honduras. In: *Génétique et Population*. Paris: Presses Universitaires de France (TODO: verify editors and pages). |

### 2.2 Wild populations

| Population | Data, status | N | Comparable values | Citation |
|---|---|---|---|---|
| Soay sheep, St Kilda (current) | https://raw.githubusercontent.com/eamittell/PriorViabilitySelectionSoaySheep/main/SheepPedigreeRandomIds_May2025.csv (`animal,dam,sire`, no sex). GPL-3. Status: fetched. | 14,334 | No statistics published for this version. Recomputed: 3,715 founders, 3,349 half-founders, maximum depth 17. | Mittell EA, Pemberton JM, Kruuk LEB, Morrissey MB (2025). Unmeasured prior viability selection resolves the paradox of stasis for body size in wild Soay sheep. *PNAS* 122(48):e2513969122. https://doi.org/10.1073/pnas.2513969122 |
| Soay sheep (Bérénos pedigrees 1 and 2) | Dryad https://doi.org/10.5061/dryad.367s2 (CC0): `pedigree1dryad.txt` and `pedigree2dryad.txt` (`ID, MUMID, FATHER`, no sex), and the ASReml-R inverse relationship matrices of both (`inversepedigree1.RData`, `inversepedigree2.RData`). Status: fetched; in the harness. | 5,068 and 6,740 | Bérénos 2014, Table 2 (pedantics), Pedigree 1 / Pedigree 2: 5,068 / 6,740 records, 4,373 / 5,981 maternities, 2,253 / 4,593 paternities, 129 / 349 full-sibs, 13,367 / 19,564 maternal and 13,451 / 48,138 paternal half-sibs, maximum depth 9 / 10, 478 / 404 founders, nonzero F 120 / 813, F > 0.125 8 / 27, mean pairwise relatedness 0.00295 / 0.00587. The "6,740 individuals, depth 10" is Pedigree 2, not a later version. Johnston 2016 (Methods) describes the pedigree as "5516 individuals with 4531 maternal and 4158 paternal links", which matches neither deposited file. pedsum reproduces every count except the half-sibs (`benchmarks/published/differences.md`, §6), and its F equals ASReml's for every individual. | Bérénos C, Ellis PA, Pilkington JG, Pemberton JM (2014). Estimating quantitative genetic parameters in wild populations: a comparison of pedigree and genomic approaches. *Mol Ecol* 23(14):3434–3451. https://doi.org/10.1111/mec.12827 · Johnston SE, Bérénos C, Slate J, Pemberton JM (2016). Conserved genetic architecture underlying individual recombination rate variation in a wild population of Soay sheep (*Ovis aries*). *Genetics* 203(1):583–598. https://doi.org/10.1534/genetics.115.185553 · James C, Pemberton JM, Navarro P, Knott S (2024). Investigating pedigree- and SNP-associated components of heritability in a wild population of Soay sheep. *Heredity* 132(4):202–210. https://doi.org/10.1038/s41437-024-00673-6 · Morrissey MB, Wilson AJ (2010). pedantics: an R package for pedigree-based genetic simulation and pedigree manipulation, characterization and viewing. *Mol Ecol Resour* 10(4):711–719. https://doi.org/10.1111/j.1755-0998.2009.02817.x |
| Rum red deer | Figshare, `ped_anon.txt`, https://doi.org/10.6084/m9.figshare.25053941 (CC BY 4.0). The `*_anon` columns code calves, mothers and sires separately, so they do not link across generations; use `Code`, `MumCode`, `Sire`. No sex column. Status: fetched; in the harness. | 6,048 rows | Walling 2011 (Results, "Levels of inbreeding"), older pedigree, calves born 1980–2010: with both parents and at least one grandparent known, 405/1,848 (21.9%) have F > 0, mean F 0.00724; with all four grandparents known, 346/821 (42.1%), mean F 0.0128. Hewett 2024 reports no pedigree statistics (it uses FROH). *Recomputed* on this file, all years: 1,552/3,093 (50.2%), mean F 0.01151; four grandparents, 1,312/1,861 (70.5%), mean F 0.01605. The file has no birth year, so Walling's subset cannot be rebuilt. | Hewett AM, Johnston SE, Morris A, Morris S, Pemberton JM (2024). Genetic architecture of inbreeding depression may explain its persistence in a population of wild red deer. *Mol Ecol* 33(9):e17335. https://doi.org/10.1111/mec.17335 · Walling CA, Nussey DH, Morris A, Clutton-Brock TH, Kruuk LEB, Pemberton JM (2011). Inbreeding depression in red deer calves. *BMC Evol Biol* 11:318. https://doi.org/10.1186/1471-2148-11-318 |
| Mandarte song sparrow | Dryad https://doi.org/10.5061/dryad.p7p1jb3 (CC0), `Wolak_et_al_SOSP_fitness_QG.zip`: per-analysis data with each bird's `f_coeff` and `immGG`, and lower-triangle A⁻¹ lists, but no parent table. The harness rebuilds the pedigree from the fitness A⁻¹. https://doi.org/10.5061/dryad.p9s04 has no individual ids. Also the GitHub repo `matthewwolak/Wolak_etal_SongSparrowFitnessQG`, described as "a restricted subset". Status: fetched; in the harness. | 3,062 in the A⁻¹ (2,821 phenotyped) | Wolak 2018, Results: 26 immigrants; "Across the 2821 individuals, mean f was 0.074 ± 0.052 (range 0.000–0.347, 7.4% zeroes)"; "mean IGG coefficient was 0.52 ± 0.13SD". pedsum's F equals F from the A⁻¹ and matches `f_coeff` for 1,883 of the 2,821; the two differ by one ancestor's link, and the published summary matches neither (`differences.md`, §8). | Wolak ME, Arcese P, Keller LF, Nietlisbach P, Reid JM (2018). Sex‐specific additive genetic variances and correlations for fitness in a song sparrow (*Melospiza melodia*) population subject to natural immigration and inbreeding. *Evolution* 72(10):2057–2075. https://doi.org/10.1111/evo.13575 · Nietlisbach P, Keller LF, Camenisch G, Guillaume F, Arcese P, Reid JM, Postma E (2017). Pedigree-based inbreeding coefficient explains more variation in fitness than heterozygosity at 160 microsatellites in a wild bird population. *Proc R Soc B* 284(1850):20162763. https://doi.org/10.1098/rspb.2016.2763 |
| Helgeland house sparrow | Dryad https://doi.org/10.5061/dryad.m0cfxpp10 (CC0): `pedigree.txt` (Sequoia SNP pedigree, `id, dam, sire`; 440 rows are Sequoia dummy parents) and `Data.txt` (the genotyped birds). Status: fetched; in the harness. | 3,556 rows (3,116 genotyped) | Pedigree for 3,116 adults; F computed with the R package `pedigree` for 1,241 individuals with at least two full ancestral generations (Methods). pedsum gives 3,116 and 1,241 with the dummy parents kept; the deposited `Estimating_pedigree_F.R` drops them, which gives 490 (`differences.md`, §7). No pedigree F is deposited. | Niskanen AK, Billing AM, Holand H, Hagen IJ, Araya-Ajoy YG, Husby A, Rønning B, Myhre AM, Ranke PS, Kvalnes T, Pärn H, Ringsby TH, Lien S, Sæther B-E, Muff S, Jensen H (2020). Consistent scaling of inbreeding depression in space and time in a house sparrow metapopulation. *PNAS* 117(25):14584–14592. https://doi.org/10.1073/pnas.1909599117 |
| Chatham Island black robin | Dryad https://doi.org/10.5061/dryad.16g74 (CC0), DatasheetC of Kennedy 2014: the whole pedigree since the 1979–82 bottleneck, with each bird's F (`IndividualF`). Dryad https://doi.org/10.5061/dryad.81tg6 (`DatasetS1.csv`, Weiser 2016) holds 1,104 of these birds, without the 33 earliest parents. Status: fetched; in the harness. | 1,348 | Per-individual F; pedsum matches `IndividualF` for all 1,348 birds and `DatasetS1` for all 1,104. Weiser's thesis (ch. 5): "Inbreeding coefficients (F) ranged from 0.25 to 0.65". Weiser counts the bottleneck pair as the 2 founders; the file has 6 rows with no known parent. | Kennedy ES, Grueber CE, Duncan RP, Jamieson IG (2013). Data from: Severe inbreeding depression and no evidence of purging in an extremely inbred wild species - the Chatham Island black robin. Dryad. https://doi.org/10.5061/dryad.16g74 · Weiser EL (2014). *Informing genetic management of small populations of threatened species*. PhD thesis, University of Otago, Dunedin. https://hdl.handle.net/10523/4852 · Weiser EL, Grueber CE, Kennedy ES, Jamieson IG (2016). Unexpected positive and negative effects of continuing inbreeding in one of the world's most inbred wild animals. *Evolution* 70(1):154–166. https://doi.org/10.1111/evo.12840 · Kennedy ES, Grueber CE, Duncan RP, Jamieson IG (2014). Severe inbreeding depression and no evidence of purging in an extremely inbred wild species—the Chatham Island black robin. *Evolution* 68(4):987–995. https://doi.org/10.1111/evo.12315 |
| Pyrenean brown bear | Dryad https://doi.org/10.5061/dryad.w9ghx3g1s: per-trait tables (mother per bear, father per litter, `Inbreeding_individual`), with no pedigree file. Its F includes microsatellite-corrected founder relatedness and is rounded to 4 decimals. Status: fetched, no pedigree. | about 100–150 | Depth 0–6 generations; mean 1.30 complete generations; mean 3.11 maximum generations; F 0–0.375 | Auclair L, Vanpé C, Chapron G, Quenette P-Y, Robert A (2025). Inbreeding depression across multiple life-history traits in a long-lived mammal. *Mol Ecol* 34(21):e70123. https://doi.org/10.1111/mec.70123 |
| Florida scrub-jay | Dryad https://doi.org/10.5061/dryad.z612jm6j0 (CC0): `cr_ped_20240602.tsv` (`ID, SIRE_ID, DAM_ID, SEX`; 17 parents of translocated birds have no row) and `cr_ped_20230512_relatedness_matrix.txt` (the authors' nadiv `makeA()` matrix). Status: fetched; in the harness. | 678 rows (695 with the absent parents) | One breeding pair (RLS-K and WSA-K) "collectively accounted for 24% (SD = 0.06) of the expected CR population founder ancestry, with a maximum contribution of 32% in 2017" (Results; gap B1). 74 founding ancestors (pedsum: 106 rows with no known parent). F from the deposited A matches pedsum for 499 of 678 birds; the A has the nadiv 2.17.2 `makeA()` bug, and pedsum's F matches an independent tabular A (`differences.md`, §9). | Linderoth T, Deaner L, Chen N, Bowman R, Boughton RK, Fitzpatrick SW (2025). Translocations spur population growth but fail to prevent genetic erosion in imperiled Florida Scrub-Jays. *Curr Biol* 35(6):1391–1399.e6. https://doi.org/10.1016/j.cub.2025.01.058 · Hunter DC, Pemberton JM, Pilkington JG, Morrissey MB (2019). Pedigree-based estimation of reproductive value. *J Hered* 110(4):433–444. https://doi.org/10.1093/jhered/esz033 |
| Southern Resident killer whales | https://raw.githubusercontent.com/noaa-nwfsc/srkw-status/main/data/orca.rda (mothers only, no father column). GPL-3. Status: fetched. | 227 | Published: 4 inbred offspring; two males sired 52% of sampled offspring. The sires are not in the file. | Ford MJ, Parsons KM, Ward EJ, Hempelmann JA, Emmons CK, Hanson MB, Balcomb KC, Park LK (2018). Inbreeding in an endangered killer whale population. *Anim Conserv* 21(5):423–432. https://doi.org/10.1111/acv.12413 |
| Seychelles warbler | Dryad https://doi.org/10.5061/dryad.vt4b8gtr1 (CC0), `Telo_h2_Pruned_Pedigree_2020.csv` (`id, mum, dad`): the pedantics-pruned pedigree. Status: fetched; in the harness. | 1,482 | Preprint SI Table S3 (pruned pedigree, pedantics): 1,482 records, 1,217 maternities, 1,268 paternities, 696 full sibs, 1,669 maternal and 2,454 paternal half-sibs, 214 founders, 210 with F > 0, 41 with F > 0.125, mean pairwise relatedness 0.011. The preprint says the "pedigree contains 10 generations", with mean depth 3.4. pedsum reproduces every count except the half-sibs (`differences.md`, §6). | Sparks AM, Spurgin LG, van der Velde M, Fairfield EA, Komdeur J, Burke T, Richardson DS, Dugdale HL (2022). Telomere heritability and parental age at conception effects in a wild avian population. *Mol Ecol* 31(23):6324–6338. https://doi.org/10.1111/mec.15804 · Sparks A, Spurgin L, van der Velde M, Fairfield E, Komdeur J, Burke T, Richardson D, Dugdale H (2020). Telomere heritability and parental age at conception effects in a wild avian population. Preprint, EcoEvoRxiv. https://doi.org/10.32942/osf.io/eq2af · Morrissey MB, Wilson AJ (2010). pedantics: an R package for pedigree-based genetic simulation and pedigree manipulation, characterization and viewing. *Mol Ecol Resour* 10(4):711–719. https://doi.org/10.1111/j.1755-0998.2009.02817.x |
| Scandinavian arctic fox | Dryad https://doi.org/10.5061/dryad.6g8t8 (CC0), `Submitted to Dryad.xlsx` (sheet `Blad1`: `ID, Sex, F, Sire, Dam`). Fox5 is listed as her own dam; the harness makes her a founder. Status: fetched; in the harness. | 247 rows (252 with the absent sires) | Abstract: 33 litters, 205 individuals, founded by 5 individuals. Mean F about 0.125 (TODO: verify; the sheet's F averages 0.055). The sheet's F matches pedsum for 207 of the 247; the rest use parentage the sheet lacks (`differences.md`, §11). | Norén K, Godoy E, Dalén L, Meijer T, Angerbjörn A (2016). Inbreeding depression in a critically endangered carnivore. *Mol Ecol* 25(14):3309–3318. https://doi.org/10.1111/mec.13674 |
| Kalahari meerkats | Dryad https://doi.org/10.5061/dryad.h90j32v2 (CC0), `MixedModelData.xls`: each pup's F (`PupF`), its mother's F and its mother (`Mum`), but no sire column, so it is not a pedigree. Status: fetched, no pedigree. | — | Of the 1,583 pups born 1993–2009, 474 of the 1,073 with a computable F (44%) have F > 0 (Results) | Nielsen JF, English S, Goodall-Copestake WP, Wang J, Walling CA, Bateman AW, Flower TP, Sutcliffe RL, Samson J, Thavarajah NK, Kruuk LEB, Clutton-Brock TH, Pemberton JM (2012). Inbreeding and inbreeding depression of early life traits in a cooperative mammal. *Mol Ecol* 21(11):2788–2804. https://doi.org/10.1111/j.1365-294X.2012.05565.x |
| Kluane red squirrel | Dryad https://doi.org/10.5061/dryad.b064t9c5 (CC0), `pedigree.csv` (`ID, SIRE.ID, DAM.ID, Sex, BYEAR`). Status: fetched; in the harness. | 928 | No pedigree statistics found. The harness checks counts, and F against an independent recursion. | Taylor RW, Boon AK, Dantzer B, Réale D, Humphries MM, Boutin S, Gorrell JC, Coltman DW, McAdam AG (2012). Low heritabilities, but genetic and maternal correlations between red squirrel behaviours. *J Evol Biol* 25(4):614–624. https://doi.org/10.1111/j.1420-9101.2012.02456.x |

### 2.3 Captive, aquaculture and livestock

| Population | Data, status | Comparable values | Citation |
|---|---|---|---|
| Steelhead hatchery | Dryad https://doi.org/10.5061/dryad.bn249 (CC0), `MEC-12-0879_DRYAD_phenotype_data.csv`: 6,173 returning adults with `Dam` and `Sire`. Status: fetched; in the harness. | 6,602 fish over 4 generations; Ne 107.9; 15.7% of F4 have F > 0. The deposit is a subset (6,173 fish plus 4 sires without rows, deepest at depth 3) with no generation column, so none of these can be rebuilt; pedsum's F equals an independent recursion. | Naish KA, Seamons TR, Dauer MB, Hauser L, Quinn TP (2013). Relationship between effective population size, inbreeding and adult fitness‐related traits in a steelhead (*Oncorhynchus mykiss*) population released in the wild. *Mol Ecol* 22(5):1295–1309. https://doi.org/10.1111/mec.12185 |
| Brookfield Zoo *Peromyscus* | Dryad https://doi.org/10.5061/dryad.8q153 (CC0), `pedigree.txt`: `ID, SEX, F, TREATMENT, GEN, DAM, SIRE, …`, 11,483 rows. Status: fetched; in the harness. | 6 populations, about 20 generations; per-individual F (4 decimals) and generation. `GEN` equals pedsum's depth for all 11,483 rows. The deposited F agrees within 1e-4 for 3,844 of 11,482: it comes from another version of the pedigree, plus truncation (root cause UNVERIFIED; `differences.md`, §10). | Willoughby JR, Fernandez NB, Lamb MC, Ivy JA, Lacy RC, DeWoody JA (2015). The impacts of inbreeding, drift and selection on genetic diversity in captive breeding populations. *Mol Ecol* 24(1):98–110. https://doi.org/10.1111/mec.13020 |
| Holstein (whole-genome-sequenced pedigree) | Dryad https://doi.org/10.5061/dryad.vx0k6djq8: genotypes of the 245 sequenced animals (145 parents, 100 targets) with each one's pedigree F. The pedigree itself (Methods: "The animals are part of a pedigree containing 743 individuals") is not deposited. Status: genotypes only. | FPED for 245 sequenced animals | Alemu SW, Kadri NK, Harland C, Faux P, Charlier C, Caballero A, Druet T (2021). An evaluation of inbreeding measures using a whole-genome sequenced cattle pedigree. *Heredity* 126(3):410–423. https://doi.org/10.1038/s41437-020-00383-9 |
| PIC pig common dataset | Supplement to the G3 paper. Status: not fetched. | None published (scale and runtime only) | Cleveland MA, Hickey JM, Forni S (2012). A common dataset for genomic analysis of livestock populations. *G3* 2(4):429–435. https://doi.org/10.1534/g3.111.001453 |

---

## 3. Considered but blocked, restricted, or without a usable file

| Resource | Why not usable | Citation |
|---|---|---|
| FamiLinx (Geni.com, about 86M profiles) | familinx.org does not connect. A copy is on OSF at https://osf.io/fd25c/: `familinx.tar.xz`, 2,055,192,260 bytes, OSF sha256 `fa29b830f5f8b38a0512fa2fde0407f17d5069911b7163924472674a66b51109`. Licence CC BY-NC-SA 2.0, and the authors ask that it not be used to identify individuals. Not downloaded: no published statistic to check, and too large for the harness. | Kaplanis J, Gordon A, Shor T, Weissbrod O, Geiger D, Wahl M, Gershovits M, Markus B, Sheikh M, Gymrek M, Bhatia G, MacArthur DG, Price AL, Erlich Y (2018). Quantitative analysis of population-scale family trees with millions of relatives. *Science* 360(6385):171–175. https://doi.org/10.1126/science.aam9309 · Colasurdo A, Omenti R (2024). Using online genealogical data for demographic research: An empirical examination of the FamiLinx database. *Demographic Research* 51(41):1299–1350. https://doi.org/10.4054/DemRes.2024.51.41 |
| Kinsources.net (more than 100 anthropological kinship networks) | Reachable; each dataset exports as IUR text with a plain GET. Licence is set per dataset. "Ancien Régime" (dataset 53, CC BY-NC-ND 3.0, 5,891 individuals) is in the harness, checked against the statistics Kinsources' Puck software shows on the dataset page. | The dataset page asks to be cited as: Public Domain (2010), Ancien Régime dataset, https://www.kinsources.net/kidarep/dataset-53-ancien-regime.xhtml |
| Kinship-algorithm benchmark sets | Datasets not identified. | Kirkpatrick B, Ge S, Wang L (2019). Efficient computation of the kinship coefficients. *Bioinformatics* 35(6):1002–1008. https://doi.org/10.1093/bioinformatics/bty725. Preprint: arXiv:1602.04368. |
| Speke's gazelle studbook | No public file. | Templeton AR, Read B (1984). Factors eliminating inbreeding depression in a captive herd of Speke's gazelle (*Gazella spekei*). *Zoo Biol* 3(3):177–199. https://doi.org/10.1002/zoo.1430030302 |
| Scandinavian wolves | No public file. Published mean F among breeding pairs 0.25–0.30 (TODO: verify). | Åkesson M, Liberg O, Sand H, Wabakken P, Bensch S, Flagstad Ø (2016). Genetic rescue in a severely inbred wolf population. *Mol Ecol* 25(19):4745–4756. https://doi.org/10.1111/mec.13797 |
| ENDOG example data | Moved to https://www.ucm.es/juanpablogutierrez. The User's Guide (updated 2010-11-10) shows ENDOG's output for `ENDOG_example_input_file.xls`: fig. 7 (p. 19) N 600, mean F 3.63%, mean maximum generations 3.60, Ne 35.51; figs. 17–18 (p. 24) base population 169, fe 67.73, 92 ancestors, fa 25, 10 ancestors explain 50%. A scratch run of pedsum on worksheet `RENUMBERED` gives N 600, mean F 0.036256 and mean maximum depth 3.5967. Not in the harness: the file is an `.xls` inside a `.CAB` inside a RAR archive. Figs. 17–18 use worksheet `RENUMBERED_S`, where animal 27 has mother = father, which `validate` rejects. | Gutiérrez JP, Goyache F (2005). A note on ENDOG: a computer program for analysing pedigree information. *J Anim Breed Genet* 122(3):172–176. https://doi.org/10.1111/j.1439-0388.2005.00512.x |
| CFC example data | Software site offline. | Sargolzaei M, Iwaisaki H, Colleau JJ (2006). CFC: a tool for monitoring genetic diversity. *Proc. 8th World Congress on Genetics Applied to Livestock Production*, Belo Horizonte (TODO: verify whole entry). |
| PyPedal example pedigrees | Fetched from the 2.0.3 release tarball on SourceForge; the Boichard pedigrees are in the harness (§1.5). | No citation collected. |
| AGHmatrix `ped.mrode` | Duplicate of Mrode (1.5). | Amadeu RR, Garcia AAF, Munoz PR, Ferrão LFV (2023). AGHmatrix: genetic relationship matrices in R. *Bioinformatics* 39(7):btad445. https://doi.org/10.1093/bioinformatics/btad445 |
| Restricted human cohorts: Hutterites, Old Order Amish, Utah Population Database, full BALSAC, deCODE (Iceland), Framingham | Access by application only. | No citation collected. |
| Pedigrees with no public file found: Tristan da Cunha, Pitcairn, Wright's shorthorn bull Comet, Rothschild, Mennonite, Dutch genealogies | No public file. | No citation collected. |
| Long-term wild studies with data on request only: Wytham great tits (SPI-Birds), collared flycatcher, Cayo Santiago macaques, Amboseli baboons, Gombe chimpanzees, takahē, kākāpō (Māori data governance), Mauritius kestrel, Alpine ibex, superb fairy-wren, Isle Royale wolves, Ram Mountain bighorn sheep | Not public, or no pedigree file found. | No citation collected. |
| Zoo and conservation studbooks: Mexican wolf, California condor, Przewalski's horse, Florida panther, dog breed studbooks; PMx examples; mouse wheel-running lines | No public file found. | No citation collected. |
