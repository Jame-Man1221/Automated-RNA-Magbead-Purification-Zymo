# TEAM 1 RNA Purification & Fluorescent Quantification 

### Authors: Julija Gellere, Aryaan Kumar, Karen Leung, Julia Purrinos

## Introduction
For its S5 project the 2024 Megatron team successfully automated the [Zymo protocol for RNA purification](https://files.zymoresearch.com/protocols/_r2132_r2133_quick-rna_magbead.pdf).
The team developed two protocol versions, both capable of handling up to 48 samples. 
- Multiples of 8 samples :  RNA purification for sample inputs in multiples of 8. 
- Custom Sample Protocol :  RNA purification for any number of samples (code works but much more complex than Zymo).

The team has also produced code for an RNA fluorescence verification protocol  - designed to quantify the amount of RNA/DNA in a given sample. This can be used to optimise experimental and purification steps for higher DNA/RNA yield.

## Contents of file
Team 1 file consists of 9 documents
- Code_Multiples_of_8_RNA_Purification.py         - Zymo protocol handling up to 48 samples in multiples of 8.
- pseudocode_8_Zymo_Mag_RNA_Purification.pdf      - pseudocode for Code_Multiples_of_8_RNA_Purification.py
- Simulation_Multiples_of_8_RNA_Purification.py   - simulation of Code_Multiples_of_8_RNA_Purification.py

- Code_Custom_Tips_RNA_Purification.py            - Zymo protocol handling any number of samples up to 48.
- Pseudocode_Custom_Tips_RNA_Purification.py      - pseudocode for Code_Custom_Tips_RNA_Purification.py
- Simulation_Custom_Tips_RNA_Purification.py      - simulation of Code_Custom_Tips_RNA_Purification.py

- Code_Fluorescent_RNA_Quantification.py          - RNA fluorescence verification protocol.
- Pseudocode_fluorescent_RNA_quantification.pdf   - pseudocode for RNA fluorescence verification protocol.
- Simulation_Flourescent_RNA_Quantification.py    - simulation of RNA fluorescence verification protocol.

Note that the simulation codes have already been set with original labware names in order to simulate the protocols, but still require a user input for number of samples and elution volume.

 
## RNA Purification Overview

### Code Setup
To tailor the protocol to your experiment define number of samples and elution volume in the user input section at the beginning of the code.

### Deck set up
<img src="images/RNA_deck.png" alt="Total RNA Purification" width="1200" height="600">

### Sample Setup
- 200uL sample should be loaded into each well of the 96 well plate by column (i.e. fill column A from the top, then B etc.) to a max of 48 samples.
- The user will then edit the protocol file with the number of samples and final elution volume which can be done in notepad.
- Tips used for transferring reagents will be returned to the tip box in slot 5 for reuse in future runs of this protocol - remember to discard if fresh tips are needed.

### Reservoir Setup
Solutions required per sample:
- 200 ul RNA Lysis Buffer
- 500 ul RNA Prep Buffer
- 30 ul MagBinding Beads
- 50 ul or more RNase-Free Water
- 50 ul DNase I Reaction Mix
- 500 ul MagBead DNA/RNA Wash 1 (concentrate)
- 500 ul MagBead DNA/RNA Wash 2 (concentrate)
- 900 ul Ethanol

- Fill the multi-well reservoir (slot 1) from left to right - for reagents using two wells add a little over 12mL maximum to each well - the code will switch wells after 12mL has been transferred.

## Fluorescent Quantification Overview
The purpose of this fluorescence quantification protocol is to automate assay set up of RNA samples in order to determine their concentrations in a plate reader capable of measuring fluorescence at 492nmEx/540nmEm. We based this protocol off the [Promega Quantifluor RNA system kit](https://www.promega.co.uk/products/rna-analysis/dna-and-rna-quantitation/quantifluor-rna-system/?catNum=E3310#protocols) but it can be adapted to alternative fluorescence quantification kits.

Working solutions prepared beforehand:
- 5ml 1X TE buffer from 20X TE and nuclease-free water
- 1ml RNA standard 100ng/ul
- 24ml Quantifluor RNA dye working solution using dye and 1X TE buffer in 1:400 ratio

### Deck Set-up
<img src="images/fluorescentsetup.jpg" alt="fluorescent setup deck" width="600" height="350">

### Example Workflow for 24 Samples
<img src="images/Fluorescent_gif.gif" alt="fluorescent gif" width="600" height="400">

## Problems encountered & solutions
- Running out of liquid in reservoir wells -> implemented liquid tracking function
- Room light levels too high -> reduced time of assay setup to minimise desensitising dye
- Blow out not completely ejecting liquid -> adjusted blow out rates and volume
- Long delay in discarding tips -> reduced steps to trash bin
- Pipette hitting bottom of wells -> adjusted pipette distance from bottom
- Magnetic module rising too far -> adjusted height of magnet from base
- Used too many pipette tips -> implemented a return tips code to reuse pipette tips
- Number of samples a user can request limited to multiples of 8 -> created partial tip column pickup version of code to allow for input of any number from 1-48

## Future Work
- Streamline Custom Sample Protocol code to improve readability for users with custom sample numbers
- Mixing steps for custom sample number protocol not optimised for maximal RNA yield - must be optimised with fluorescent RNA quantification protocol
- Ensure bubbles are not formed on pipette tips after blowout - a touch tip / shake function could be used for this
- Make the DNase I reaction and subsequent washes an optional feature
- Increase plate limit in quantification protocol
- Create GUI interface to allow easy input of sample numbers
