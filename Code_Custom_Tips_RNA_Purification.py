from opentrons import protocol_api
import time

#-------INSERT SAMPLE NUMBER (MAX 48) AND ELUTION VOLUME (MAX 300 uL) BELOW--------#


sample_num=
elution_vol=


#-------INSERT SAMPLE NUMBER (MAX 48) AND FINAL ELUTION VOLUME (MAX 300 uL) ABOVE--------#

#matrix of layout of a plate
tipmatrix = [
    ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "A12"],
    ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12"],
    ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12"],
    ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12"],
    ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11", "E12"],
    ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
    ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12"],
    ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10", "H11", "H12"]
    ]

metadata = {
    # double check which API version Geoff's OT2 is using and change the code accordingly
    "protocolName": "RNA Purification",
    "description": """RNA purification protocol for up to 48 samples of 200ul with adjusted volumes for deep wells.""",
    "author": "Team1",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    
    #liquid handling
    vol_wash_1=0 #value of used wash 1
    vol_wash_2=0 #value of used wash 2
    vol_prep_buffer=0 #value of used RNA prep buffer
    res1_max = 12000 #amount filled in reservoir wells

    #mag height:
    mag_height=5.5

    #mixing timers for 'mix for x minutes' steps
    five_mins=time.time()+60*5
    ten_mins=time.time()+60*10
    twenty_mins=time.time()+60*20
    
    #TIP CALCULATOR:
    x=sample_num

    #calculate number of sample columns on plate
    sc=int(x/8)+(x%8>0) #full columns of 8 samples + partially filled column of samples (if present)
    scp=sc-1 #coordinate of last column of samples

    #calculate positions of full columns of 8 samples on plate
    fsc=int(x/8) #number of full columns of 8 samples
    
    #calculate number of samples in partially filled column, and y coordinate needed to pick up correct number of tips for partial column
    pc=x%8 #number of samples in last column
    pcp=8-pc #position needed for 8 channel pipette to pick up correct number of tips for partially filled column

    #coordinates of partial tip sample wells and tips
    pc_x=scp #partially filled column x coordinate
    pc_y=pcp #y coordinate needed to pick up correct tip number for partially filled column
        
    # Load labware
    #reservoirs
    res1 = protocol.load_labware("4ti0131_12_reservoir_21000ul", 1)  
    res2 = protocol.load_labware("agilent_1_reservoir_290ml", 2)
    trash1 = protocol.load_labware("agilent_1_reservoir_290ml", 3)

    #tip boxes for sample handling
    tip_box_1 = protocol.load_labware("opentrons_96_tiprack_300ul", 4)
    tip_box_2 = protocol.load_labware("opentrons_96_tiprack_300ul", 6)
    #Tip box for transferring buffers etc.
    tip_box_tran = protocol.load_labware("opentrons_96_tiprack_300ul", 5)

    #magnetic module and loaded 96 well plate
    mag_module = protocol.load_module("magdeck", 7)
    mag_plate = mag_module.load_labware('4ti0136_96_wellplate_2200ul')

    #sample prep and elution 96 well plates
    prep_plate = protocol.load_labware('4ti0136_96_wellplate_2200ul', 8)
    elution_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 9)
    
    # Load pipette
    left_pipette = protocol.load_instrument(
        "p300_multi_gen2", 
        "left", 
        tip_racks=[tip_box_1, tip_box_2, tip_box_tran]  # Include both tip boxes
    )
    
    #flow rates
    left_pipette.flow_rate.aspirate = 100
    left_pipette.flow_rate.dispense = 100
    left_pipette.flow_rate.blow_out = 200

    high=1.8
    normal=1.0
    slow=0.5
    vslow=0.25

    # Reservoir Allocation
    #supernatant bin reservoir
    trashbin = trash1.wells()[0]
    #reagents
    lysis_buffer = res1["A1"] #uses 1st column of transfer tips
    ethanol = res2["A1"] #uses 2nd column of transfer tips
    mag_beads = res1["A2"] #uses 3rd column of transfer tips
    wash_1 = [res1["A3"], res1["A4"]] #uses 4th column of transfer tips
    wash_2 = [res1["A5"], res1["A6"]] #uses 5th column of transfer tips
    dnase_mix = res1["A7"] #uses 6th column of transfer tips
    prep_buffer = [res1["A8"], res1["A9"]] #uses 7th column of transfer tips
    elution_water = res1["A10"] #uses 8th column of transfer tips

    # Liquid tracking for wells
    #wells for step 5
    def source_wash_1(res1_max, vol_wash_1, wash_1):
        if vol_wash_1 <= res1_max: #detects if well is empty
            return (wash_1[0]) #if not empty, keep using well
        else: 
            return (wash_1[1]) #if empty, switch to next well
    #wells for step 6
    def source_wash_2(res1_max, vol_wash_2, wash_2):
        if vol_wash_2 <= res1_max: #detects if well is empty
            return (wash_2[0]) #if not empty, keep using well
        else: 
            return (wash_2[1]) #if empty, switch to next well
    #wells for step 9
    def source_prep_buffer(res1_max, vol_prep_buffer, prep_buffer):
        if vol_prep_buffer <= res1_max: #detects if well is empty
            return (prep_buffer[0])  #if not empty, keep using well
        else: 
            return (prep_buffer[1]) #if empty, switch to next well

    #Just in case
    mag_module.disengage()
    
### Step 1: Add 200 µl RNA Lysis Buffer to 200 µl sample and mix well
    #Add lysis buffer to full column(s) of sample
    if x>=8: #(if x>=8) performs step for any full columns of 8 samples
        #pick up column of lysis buffer transfer tips from column 1 of transfer tip box
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][0]])
        #transfer 200ul lysis buffer to each column of full samples (fsc)
        for row in range(fsc):
            left_pipette.aspirate(200, lysis_buffer.bottom(1))
            left_pipette.dispense(200, prep_plate.rows()[0][row].top(2)) 
            left_pipette.blow_out(prep_plate.rows()[0][row].top(2))
        #return lysis buffer transfer tips to column 1 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[0][0]])

    #Mix full column(s) of samples sequentially using assigned sample tips
        for row in range(fsc):
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row]]) #pick up new sample tips assigned to each well
            left_pipette.mix(3, 150, prep_plate.rows()[0][row].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_1[tipmatrix[0][row]]) #return sample tips for next step

    #Add lysis buffer to partially filled column of sample
    if x%8>0: #(if x%8>0) performs step for partially filled column of samples (scp)
        #pick up tips from column 1 of transfer tip box at y coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][0]])
        #transfer 200ul lysis buffer to partially filled sample column (scp)
        left_pipette.aspirate(200, lysis_buffer.bottom(1))
        left_pipette.dispense(200, prep_plate.rows()[0][scp].top(2))
        left_pipette.blow_out(prep_plate.rows()[0][scp].top(2))
        #return lysis buffer transfer tips to column 1 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][0]])

    #Mix partially filled column of samples with assigned mixing tips
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x]]) #pick up new sample tip(s) assigned to each well
        left_pipette.mix(3, 200, prep_plate.rows()[0][scp].bottom(1), rate=high)
        left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x]]) #return sample tip(s) for next step

### Step 2: Add 400 µl ethanol (95-100%) to the sample and mix well
    #Add EtOH to full column(s) of sample
    if x>=8:
        #pick up column of EtOH transfer tips from column 2 of transfer tip box
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][1]])
        #transfer 400uL EtOH to each full column(s) of samples (fsc)
        for row in range(fsc):
            for i in range(2): #transfer 200uL EtOH twice for 400ul total (using 300ul tips)
                left_pipette.aspirate(200, ethanol.bottom(1))
                left_pipette.air_gap(50)
                left_pipette.dispense(250, prep_plate.rows()[0][row].top(2))
                left_pipette.blow_out(prep_plate.rows()[0][row].top(2))
        #return EtOH transfer tips to column 2 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[0][1]])
        
    #Mix full column(s) of samples sequentially using assigned sample tips
        for row in range(fsc): 
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row]]) #pick up assigned sample tips from previous step
            left_pipette.mix(5, 300, prep_plate.rows()[0][row].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_1[tipmatrix[0][row]]) #return sample tips for next step

    #Add EtOH to partially filled column of sample
    if x%8>0:
        #pick up EtOH transfer tip(s) from column 2 of transfer tip box at coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][1]])
        #transfer 400uL EtOH to partial sample column (scp)
        for i in range(2): #transfer 200uL EtOH twice for 400ul total (using 300ul tips)
            left_pipette.aspirate(200, ethanol.bottom(1))
            left_pipette.air_gap(50)
            left_pipette.dispense(250, prep_plate.rows()[0][scp].top(2))
            left_pipette.blow_out(prep_plate.rows()[0][scp].top(2))
        #return EtOH transfer tip(s) to column 2 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][1]])
        
    #Mix partially filled column of samples using assigned sample tips
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x]]) #pick up assigned sample tip(s) from previous step
        left_pipette.mix(5, 300, prep_plate.rows()[0][scp].bottom(1), rate=high)
        left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x]]) #return sample tip(s) from previous step
        
### Step 3: Add 30 µl MagBinding Beads and mix well for 20 minutes
    #Mix then add MagBeads to full column(s) of sample
    if x>=8:
        #pick up column of MagBead transfer tips from column 3 of transfer tip box
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][2]])
        #Mix then transfer 30ul MagBeads to each full column of samples
        for row in range(fsc):            
            left_pipette.mix(5, 30, mag_beads.bottom(1), rate=high)
            left_pipette.aspirate(30, mag_beads.bottom(1))
            left_pipette.dispense(30, prep_plate.rows()[0][row].top())
            left_pipette.blow_out(prep_plate.rows()[0][row].top())
        #return MagBead transfer tips to column 3 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[0][2]])

    #Mix then add MagBeads to partially filled column of sample
    #(if x%8>0) performs step for partially filled column of samples (scp)
    if x%8>0:
        #pick up MagBead transfer tips from column 3 of transfer tip box at coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][2]])
        #Mix then transfer 30ul MagBeads to partially filled column
        left_pipette.mix(10, 30, mag_beads.bottom(1), rate=high)
        left_pipette.aspirate(30, mag_beads.bottom(1))
        left_pipette.dispense(30, prep_plate.rows()[0][scp].top())
        left_pipette.blow_out(prep_plate.rows()[0][scp].top())
        #return MagBead transfer tip(s) to column 3 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][2]])
        
    #Mix sample column(s) sequentially for 20 minutes
    while time.time()<twenty_mins: #loops for 20 minutes
        #Mix full column(s) of samples sequentially using assigned sample tips
        if x>=8:
            for row in range(fsc):
                left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row]]) #pick up assigned sample tips from previous step
                left_pipette.mix(3, 200, prep_plate.rows()[0][row].bottom(1), rate=high)
                left_pipette.drop_tip(tip_box_1[tipmatrix[0][row]]) #return sample tips for next step
        #Mix partially filled column of samples using assigned sample tips
        if x%8>0:
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x]]) #pick up assigned sample tip(s) from previous step
            left_pipette.mix(3, 200, prep_plate.rows()[0][scp].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x]]) #return sample tip(s) for next step
    
### Step 4: Transfer the plate/tube to the magnetic stand until beads have pelleted, then aspirate and discard the cleared supernatant      
    #Transfer full column(s) of samples to 96 well plate on magdeck
    if x>=8:
        #Mix then transfer 830uL sample from full column(s) (fsc) to 96 well plate on magdeck
        for row in range(fsc):
            #Pick up assigned sample tips from previous step
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row]])
            for i in range(3): #repeat 3 times  - using 300ul pipette to move 830 ul - 3*277          
                left_pipette.mix(3, 150, prep_plate.rows()[0][row].bottom(1), rate=high)
                left_pipette.aspirate(277, prep_plate.rows()[0][row].bottom(1))
                left_pipette.air_gap(23)
                left_pipette.dispense(300, mag_plate.rows()[0][row])
                left_pipette.blow_out(mag_plate.rows()[0][row].top())
            #Return assigned sample tips for next step
            left_pipette.drop_tip(tip_box_1[tipmatrix[0][row]])
            
    #Transfer partially filled column of samples to 96 well plate on magdeck
    if x%8>0:
        #Pick up assigned sample tip(s) from previous step
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x]])
        #Mix then transfer 830uL sample from partially filled column to 96 well plate on magdeck
        for i in range(3): #repeat 3 times  - using 300ul pipette to move 830 ul - 3*277
            left_pipette.mix(3, 150, prep_plate.rows()[0][scp], rate=high)
            left_pipette.aspirate(277, prep_plate.rows()[0][scp].bottom(1))
            left_pipette.air_gap(volume=23)
            left_pipette.dispense(300, mag_plate.rows()[0][scp])
            left_pipette.blow_out(mag_plate.rows()[0][scp].top())
        #Return assigned sample tip(s) for next step
        left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x]])

    #Pellet Magbeads for 5 minutes
    mag_module.engage(height_from_base=mag_height)
    protocol.delay(minutes=5)

    #Discard Supernatant from full column(s) of samples
    if x>=8:
        #Transfer 798uL from full column(s) of sample (fsc) to trash - leave 32ul to leave pellet
        for row in range(fsc):
            #Pick up assigned sample tips from previous step
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row]])            
            for i in range(3): #repeat 3 times  - using 300ul pipette to move 798 ul - 266*3
                left_pipette.aspirate(266, mag_plate.rows()[0][row].bottom(1))
                left_pipette.air_gap(volume=30)
                left_pipette.dispense(296, trashbin.top())
                left_pipette.blow_out(trashbin.top())
            #discard first set of sample tips to prevent contamination
            left_pipette.drop_tip()

    #Discard Supernatant from partially filled column of samples
    if x%8>0:
        #Pick up assigned sample tip(s) from previous step
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x]])
        #Transfer 798uL from partially filled column of sample (scp) to trash - leave 32ul to leave pellet        
        for i in range(3): #repeat 3 times  - using 300ul pipette to move 798 ul - 266*3
            left_pipette.aspirate(266, mag_plate.rows()[0][scp].bottom(1))
            left_pipette.air_gap(volume=30)
            left_pipette.dispense(296, trashbin.top())
            left_pipette.blow_out(trashbin.top())
        #discard first set of sample tips to prevent contamination
        left_pipette.drop_tip()

    #Disengage magnet
    mag_module.disengage()

### Step 5: Add 500 µl MagBead DNA/RNA Wash 1 and mix well. Pellet the beads and discard the supernatant
    #Add Wash 1 to full column(s) of samples
    if x>=8:
        #pick up Wash 1 transfer tips from column 4 of transfer tip box
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][3]])
        #Transfer 500uL Wash 1 to full sample column(s) (fsc)
        for row in range(fsc):
            for i in range(2):# repeat 2 times - using 300uL pipette for 500uL - 2*250
                #check reservoir has enough liquid for each transfer, if not switch to backup
                vol_wash_1 += 2000
                wash1selected=source_wash_1(res1_max, vol_wash_1, wash_1)
                left_pipette.aspirate(250, wash1selected.bottom(1))
                left_pipette.dispense(250, mag_plate.rows()[0][row].top(2)) 
                left_pipette.blow_out(mag_plate.rows()[0][row].top(2))
        #return wash 1 transfer tips to column 4 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[0][3]])
        
    #Mix full column(s) of sample sequentially using new assigned sample tips
        for row in range(fsc):
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]])  #pick up fresh assigned sample tips from other half of tip box 1
            left_pipette.mix(5, 250, mag_plate.rows()[0][row].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]]) #return sample tips for next step

    #Add Wash 1 to partially filled column of sample
    if x%8>0:
        #pick up Wash 1 transfer tips from column 4 of transfer tip box at coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][3]])
        #Transfer 500uL wash 1 to partially filled column (scp)
        for i in range(2): # repeat 2 times - using 300uL pipette for 500uL - 250*2
            #check reservoir has enough liquid for transfer, if not switch to backup
            vol_wash_1 += 250*pc
            wash1selected=source_wash_1(res1_max, vol_wash_1, wash_1)
            left_pipette.aspirate(250, wash1selected.bottom(1))
            left_pipette.dispense(250, mag_plate.rows()[0][scp].top(2)) 
            left_pipette.blow_out(mag_plate.rows()[0][scp].top(2))
        #Return Wash 1 transfer tips to column 4 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][3]])
        
    #Mix partially filled column of samples using new assigned sample tips
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #pick up fresh assigned sample tip(s) from other half of tip box 1
        left_pipette.mix(5, 250, mag_plate.rows()[0][scp].bottom(1), rate=high)
        left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #return sample tips for next step

    #Pellet samples for 5 minutes
    mag_module.engage(height_from_base=mag_height)
    protocol.delay(minutes=5)
    
    #Discard supernatant from full column(s) of samples
    if x>=8:
        #Transfer 500uL from full column(s) (fsc) to trash
        for row in range(fsc):
            #Pick up assigned sample tips from previous step
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]])
            for i in range(2): #repeat 2 times - moving 500uL with 300ul pipette - 2*250
                left_pipette.aspirate(250, mag_plate.rows()[0][row].bottom(1))
                left_pipette.dispense(250, trashbin.top()) 
                left_pipette.blow_out(trashbin.top())
            #Return assigned sample tips for next step
            left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]]) 

    #Discard supernatant from partially filled column of sample
    if x%8>0:
        #Transfer 500uL from partiallt filled column (scp) to trash
        for i in range(2): #repeat 2 times - moving 500uL with 300ul pipette - 2*250
            #Pick up assigned sample tip(s) from previous step
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])
            left_pipette.aspirate(250, mag_plate.rows()[0][scp].bottom(1))
            left_pipette.dispense(250, trashbin.top()) 
            left_pipette.blow_out(trashbin.top())
            #Return assigned sample tip(s) for next step
            left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])

    #Disengage magnet
    mag_module.disengage()
    
### Step 6: Add 500 µl MagBead DNA/RNA Wash 2 and mix well. Pellet the beads and discard the supernatant
    #Add 500uL Wash 2 to full column(s) of sample
    if x>=8:
        #Pick up Wash 2 transfer tips from column 5 of transfer tip box
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][4]])
        #Transfer 500uL Wash 2 to full sample column(s) (fsc)
        for row in range(fsc):
            for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
                #check reservoir has enough liquid for transfer, if not switch to backup
                vol_wash_2+=2000
                wash2selected = source_wash_2(res1_max, vol_wash_2, wash_2)
                left_pipette.aspirate(250, wash2selected.bottom(1))
                left_pipette.dispense(250, mag_plate.rows()[0][row].top(2)) 
                left_pipette.blow_out(mag_plate.rows()[0][row].top(2))
        #Return Wash 2 transfer tips to column 5 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[0][4]])
        
    #Mix full column(s) of samples sequentially using assigned sample tips
    for row in range(fsc):
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]]) #pick up assigned sample tips from previous step
        left_pipette.mix(3, 150, mag_plate.rows()[0][row].bottom(1), rate=high)
        left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]]) #return sample tips for next step

    #Add wash 2 to partially filled column of sample
    if x%8>0:
        #Pick up Wash 2 transfer tips from column 5 of transfer tip box at coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][4]])
        #Transfer 500uL Wash 2 to partially filled column(s) (scp)
        for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
            #check reservoir has enough liquid for transfer, if not switch to backup
            vol_wash_2+=250*pc
            wash2selected = source_wash_2(res1_max, vol_wash_2, wash_2)
            left_pipette.aspirate(250, wash2selected.bottom(1))
            left_pipette.dispense(250, mag_plate.rows()[0][scp].top(2)) 
            left_pipette.blow_out(mag_plate.rows()[0][scp].top(2))
        #Return Wash 2 transfer tips to column 5 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][4]])
        
    #Mix full column(s) of samples sequentially using assigned sample tips
    left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #pick up assigned sample tip(s) from previous step
    left_pipette.mix(3, 150, mag_plate.rows()[0][scp].bottom(1), rate=high)
    left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #return sample tip(s) for next step

    #Pellet MagBeads for 5 minutes
    mag_module.engage(height_from_base=mag_height)
    protocol.delay(minutes=5)
    
    #Discard supernatant from full column(s) of samples
    if x>=8:
        #Transfer 500uL from full column(s) of sample (fsc) to trash
        for row in range(fsc):
            #Pick up assigned sample tips from previous step
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]])
            for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
                left_pipette.aspirate(250, mag_plate.rows()[0][row].bottom(1))
                left_pipette.dispense(250, trashbin.top()) 
                left_pipette.blow_out(trashbin.top())
            #Return sample tips for next step
            left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]])

    #Discard supernatant from partially filled columns of samples
    if x%8>0:
        #Pick up assigned sample tip(s) from previous step
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])
        #Transfer 500uL from partially filled column of sample (scp) to trash
        for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
            left_pipette.aspirate(250, mag_plate.rows()[0][scp].bottom(1))
            left_pipette.dispense(250, trashbin.top()) 
            left_pipette.blow_out(trashbin.top())
        #Return assigned sample tip(s) for step
        left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])

    #Disengage Magnet
    mag_module.disengage()
    
### Steps 7-8: Add 500 µl ethanol (95-100%) and mix well. Pellet the beads and discard the supernatant (repeat twice)
    for i in range(2): #Perform EtOH wash step twice
        #Add EtOH to full column(s) of sample
        if x>=8:
            #pick up EtOH transfer tips from column 2 of transfer tip box
            left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][1]])
            #transfer 500uL EtOH to each full column of samples (fsc)
            for row in range(fsc):
                for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
                    left_pipette.aspirate(250, ethanol.bottom(1))
                    left_pipette.air_gap(50)
                    left_pipette.dispense(300, mag_plate.rows()[0][row].top(2))
                    left_pipette.blow_out(mag_plate.rows()[0][row].top(2))
            #return EtOH transfer tips to column 2 of transfer tip box
            left_pipette.drop_tip(tip_box_tran[tipmatrix[0][1]])

        #Mix full column(s) of samples sequentially using assigned sample tips
            for row in range(fsc):
                left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]]) #pick up assigned sample tips from previous step
                left_pipette.mix(5, 200, mag_plate.rows()[0][row].bottom(1), rate=high)
                left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]]) #return mixing tips for next step

        #add EtOH to partially filled column of sample
        if x%8>0:
            #pick up EtOH transfer tips from column 2 of transfer tip box at coordinate [pc_y]
            left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][1]])
            #transfer 500uL EtOH to partially filled column of samples (scp)
            for i in range(2): #repeat 2 times to transfer 500uL with 300ul pipette - 250*2
                left_pipette.aspirate(250, ethanol.bottom(1))
                left_pipette.air_gap(50)
                left_pipette.dispense(300, mag_plate.rows()[0][scp].top(2)) 
                left_pipette.blow_out(mag_plate.rows()[0][scp].top(2))
            #return EtOH transfer tip(s) to column 2 of transfer tip box
            left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][1]])

        #Mix partially filled column of samples using assigned sample tips
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #pick up assigned sample tips from previous step
            left_pipette.mix(5, 200, mag_plate.rows()[0][scp].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #return sample tips for next step


        #Pellet MagBeads for 5 minutes
        mag_module.engage(height_from_base=mag_height)
        protocol.delay(minutes=5)
        
    #discard supernatant of full column(s)
        if x>=8:
            #Transfer 500uL from full column(s) of sample (fsc) to trash
            for row in range(fsc):
                #Pick up assigned sample tips from previous step
                left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]])
                for i in range(2): #repeat 2 times to transfer 500uL with 300ul pipette - 250*2
                    left_pipette.aspirate(250, mag_plate.rows()[0][row].bottom(1))
                    left_pipette.air_gap(50)
                    left_pipette.dispense(300, trashbin.top()) 
                    left_pipette.blow_out(trashbin.top())
                #Return sample tips for next step
                left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]])

    #discard supernatant of partial column
        if x%8>0:
            #Pick up assigned sample tip(s) from previous step
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])
            #Transfer 500uL from partially filled column of sample (scp) to trash
            for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
                left_pipette.aspirate(250, mag_plate.rows()[0][scp].bottom(1))
                left_pipette.air_gap(50)
                left_pipette.dispense(300, trashbin.top()) 
                left_pipette.blow_out(trashbin.top())
            #Return sample tip(s) for next step
            left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])

        #Disable magnet
        mag_module.disengage()

###Step 9: Add 50 µl DNase I reaction mix & mix for 10 mins, then add RNA prep buffer and mix well for 10 minutes
    #transfer DNase to full column(s)
    if x>=8:
        #pick up DNase transfer tips from column 6 of transfer tip box
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][5]])
        #Transfer 50uL DNase I reaction mix to full column(s) of sample (fsc)
        for row in range(fsc): 
            left_pipette.aspirate(50, dnase_mix.bottom(1))
            left_pipette.dispense(50, mag_plate.rows()[0][row].top(2))
            left_pipette.blow_out(mag_plate.rows()[0][row].top(2))
        left_pipette.drop_tip(tip_box_tran[tipmatrix[0][5]])
    #transfer DNase to partial column
    if x%8>0:
        #pick up DNase transfer tips from column 6 of transfer tip box at coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][5]])
        #Transfer 50uL DNase I reaction mix to partially full column of sample (scp)
        left_pipette.aspirate(50, dnase_mix.bottom(1))
        left_pipette.dispense(50, mag_plate.rows()[0][scp].top(2))
        left_pipette.blow_out(mag_plate.rows()[0][scp].top(2))
        left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][5]])

    #Mix sample column(s) sequentially for ten minutes
    while time.time()<ten_mins: #loop for ten minutes
        #Mix full column(s) of sample sequentially
        if x>=8:
            for row in range(fsc):
                left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]]) #pick up assigned sample tips from previous step
                left_pipette.mix(3, 50, mag_plate.rows()[0][row].bottom(1), rate=high)
                left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]]) #return sample tips for next step

        #Mix partially filled column of sample
        if x%8>0:
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #pick up assigned sample tip(s) from previous step
            left_pipette.mix(3, 50, mag_plate.rows()[0][scp].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #return sample tip(s) for next step

    #Add RNA prep buffer to full column(s) of sample
    if x>=8:
        #Pick up prep buffer transfer tips from column 7 of transfer tip box
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][6]])
        #Transfer 500uL RNA prep buffer to full column(s) of sample (fsc)
        for row in range(fsc):
            for i in range(2): #repeat 2 times to transfer 500uL with 300ul pipette - 250*2
                #check reservoir has enough liquid for transfer, if not switch to backup
                vol_prep_buffer+=2000
                prepbufferselected = source_prep_buffer(res1_max, vol_prep_buffer, prep_buffer)
                left_pipette.aspirate(250, prepbufferselected.bottom(1))
                left_pipette.dispense(250, mag_plate.rows()[0][row].top(2))
                left_pipette.blow_out(mag_plate.rows()[0][row].top(2))
        #Return RNA prep buffer transfer tips to column 7 of transfer tip box at coordinate [pc_y]
        left_pipette.drop_tip(tip_box_tran[tipmatrix[0][6]])

    #Add RNA prep buffer to partially filled column of sample
    if x%8>0:
        #pick up RNA prep buffer transfer tips from column 7 of transfer tip box at coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][6]])
        #Transfer 500uL RNA prep buffer to partially filled column of sample (scp)
        for i in range(2): #repeat 2 times to transfer 500uL with 300ul pipette - 250*2
            #check reservoir has enough liquid for transfer, if not switch to backup
            vol_prep_buffer+=250*pc
            prepbufferselected = source_prep_buffer(res1_max, vol_prep_buffer, prep_buffer)
            left_pipette.aspirate(250, prepbufferselected.bottom(1))
            left_pipette.dispense(250, mag_plate.rows()[0][scp].top(2))
            left_pipette.blow_out(mag_plate.rows()[0][scp].top(2))
        #Return RNA prep buffer transfer tips to column 7 of transfer tip box at coordinate [pc_y]
        left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][6]])

    #Mix sample columns sequentially for 10 mins
    while time.time()<ten_mins: #loops for 10 minutes
        #Mix column(s) sequentially using assigned sample tips
        if x>=8:
            for row in range(fsc):
                left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]]) #pick up assigned sample tips from previous step
                left_pipette.mix(3, 250, mag_plate.rows()[0][row].bottom(1), rate=high)
                left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]]) #return sample tips for next step
        #Mix partially filled column using assigned sample tips
        if x%8>0:
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #pick up assigned sample tip(s) from previous step
            left_pipette.mix(3, 250, mag_plate.rows()[0][scp].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #return sample tips for next step

    #Discard supernatant of full column(s) of sample
    if x>=8:
        #Transfer 520uL from full column(s) of sample (fsc) to trash - leaving 30uL to keep MagBeads
        for row in range(fsc):
            #Pick up assigned sample tips from previous step
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]])
            for i in range(2): #repeat twice to transfer 520uL with 300ul pipette - 260*2
                left_pipette.aspirate(260, mag_plate.rows()[0][row].bottom(1))
                left_pipette.dispense(260, trashbin.top()) 
                left_pipette.blow_out(trashbin.top())
            #Return sample tips for next step
            left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]])

    #Discard supernatant of partially filled column of sample
    if x%8>0:
        #Pick up assigned sample tip(s) from previous step
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])
        #Transfer 520uL from partially filled column of sample (scp) to trash - leaving 30uL to keep MagBeads
        for i in range(2): #repeat twice to transfer 520uL with 300ul pipette - 260*2
            left_pipette.aspirate(260, mag_plate.rows()[0][scp].bottom(1))
            left_pipette.dispense(260, trashbin.top()) 
            left_pipette.blow_out(trashbin.top())
        #Return sample tip(s) for next step
        left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])

    #Disengage magnet
    mag_module.disengage()

### Step 10: Add 500 µl ethanol (95-100%) and mix well. Pellet the beads and discard the supernatant. Repeat EtOH wash.
    for i in range(2): #Perform wash step twice
        #Add EtOH to full column(s) of sample
        if x>=8:
            #pick up EtOH transfer tips from column 2 of transfer tip box at coordinate [pc_y]
            left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][1]])
            #transfer 500uL EtOH to each full column of samples (fsc)
            for row in range(fsc):
                for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
                    left_pipette.aspirate(250, ethanol.bottom(1))
                    left_pipette.air_gap(50)
                    left_pipette.dispense(300, mag_plate.rows()[0][row].top(2)) 
                    left_pipette.blow_out(mag_plate.rows()[0][row].top(2))
            #return EtOH transfer tip(s) to column 2 of transfer tip box
            left_pipette.drop_tip(tip_box_tran[tipmatrix[0][1]])

            #Mix full column(s) of sample sequentially using assigned sample tips
            for row in range(fsc):
                left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]]) #pick up assigned sample tips from previous step
                left_pipette.mix(3, 150, mag_plate.rows()[0][row].bottom(1), rate=high)
                left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]]) #return sample tips for next step

    #Add EtOH to partially filled column of sample
        if x%8>0:
            #pick up EtOH transfer tips from column 2 of transfer tip box at coordinate [pc_y]
            left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][1]])
            #transfer 500uL EtOH to partially filled column of samples (scp)
            for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
                left_pipette.aspirate(250, ethanol.bottom(1))
                left_pipette.air_gap(50)
                left_pipette.dispense(300, mag_plate.rows()[0][scp].top(2)) 
                left_pipette.blow_out(mag_plate.rows()[0][scp].top(2))
            #return EtOH transfer tip(s) to column 2 of transfer tip box
            left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][1]])

            #Mix partially filled column of sample using assigned sample tips
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #pick up assigned sample tip(s) from previous step
            left_pipette.mix(3, 150, mag_plate.rows()[0][scp].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]]) #return sample tip(s) for next step
            
        #Pellet MagBeads for 5 minutes
        mag_module.engage(height_from_base=mag_height)
        protocol.delay(minutes=5)

    #discard supernatant of full column(s)
        if x>=8:
            #Transfer 500uL from full columns of sample (fsc) to trash
            for row in range(fsc):
                #Pick up assigned sample tips from previous step
                left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]])
                for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
                    left_pipette.aspirate(250, mag_plate.rows()[0][row].bottom(1))
                    left_pipette.air_gap(50)
                    left_pipette.dispense(300, trashbin.top()) 
                    left_pipette.blow_out(trashbin.top())
                #Return sample tips for next step
                left_pipette.drop_tip(tip_box_1[tipmatrix[0][row+6]])

    #discard supernatant of partial column
        if x%8>0:
            #Pick up assigned sample tip(s) from previous step
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])
            #Transfer 500uL from partially filled column of sample (scp) to trash
            for i in range(2): #repeat twice to transfer 500uL with 300ul pipette - 250*2
                left_pipette.aspirate(250, mag_plate.rows()[0][scp].bottom(1))
                left_pipette.air_gap(50)
                left_pipette.dispense(300, trashbin.top()) 
                left_pipette.blow_out(trashbin.top())
            #Return sample tips for next step
            left_pipette.drop_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])

    #discard full column(s) of mixing tips to prevent contamination
    if x>=8:
        for row in range(fsc):
            left_pipette.pick_up_tip(tip_box_1[tipmatrix[0][row+6]])
            left_pipette.drop_tip()

    #discard partial column of mixing tips to prevent contamination
    if x%8>0:
        left_pipette.pick_up_tip(tip_box_1[tipmatrix[pc_y][pc_x+6]])
        left_pipette.drop_tip()

    #disengage magnet
    mag_module.disengage()

    #Dry Pellets for 10 minutes
    protocol.delay(minutes=10)

### Step 11: Add CUSTOM ul DNase/RNase free water and mix well for 5 mins to elute DNA/RNA
    #Add DNase/RNase free water to full column(s)
    if x>=8:
        #pick up DNase/RNase free water transfer tips from column 8 of transfer tip box
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[0][7]])
        #transfer 50uL DNase/RNase free water to full column(s) of sample (fsc)
        for row in range(fsc): 
            left_pipette.aspirate(elution_vol, elution_water.bottom(1))
            left_pipette.dispense(elution_vol, mag_plate.rows()[0][row].top(2))
            left_pipette.blow_out(mag_plate.rows()[0][row].top(2))
        #return DNase/RNase free water transfer tips to column 8 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[0][7]])

    #add DNase/RNase free water to partial column
    if x%8>0:
        #pick up Dnase/RNase free water transfer tips from column 8 of transfer tip box at coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_tran[tipmatrix[pc_y][7]])
        #Transfer 50uL Dnase/RNase free water to partially filled column of sample
        left_pipette.aspirate(elution_vol, elution_water.bottom(1))
        left_pipette.dispense(elution_vol, mag_plate.rows()[0][scp].top(2))
        left_pipette.blow_out(mag_plate.rows()[0][scp].top(2))
        #pick up DNase/RNase free water transfer tips from column 8 of transfer tip box
        left_pipette.drop_tip(tip_box_tran[tipmatrix[pc_y][7]])

    #Mix column(s) sequentially for 5 minutes
    while time.time()<five_mins: #loop for 5 minutes
        #Mix full column(s) of sample sequentially using assigned sample tips
        if x>=8:
            for row in range(fsc):
                left_pipette.pick_up_tip(tip_box_2[tipmatrix[0][row]]) #pick up assigned sample tips from previous step
                left_pipette.mix(3, elution_vol, mag_plate.rows()[0][row].bottom(1), rate=high)
                left_pipette.drop_tip(tip_box_2[tipmatrix[0][row]]) #return assigned sample tips for next step
        #Mix partially filled column of sample using assigned sample tips
        if x%8>0:
            left_pipette.pick_up_tip(tip_box_2[tipmatrix[pc_y][pc_x]]) #pick up assigned sample tip(s) from previous step
            left_pipette.mix(3, elution_vol, mag_plate.rows()[0][scp].bottom(1), rate=high)
            left_pipette.drop_tip(tip_box_2[tipmatrix[pc_y][pc_x]]) #return assigned sample tip(s) for next step

    #Pellet MagBeads for 5 minutes
    mag_module.engage(height_from_base=mag_height)
    protocol.delay(minutes=5)

### Step 12: Transfer the eluted RNA to the elution plate
    if x>=8:
        #Transfer full column(s) of eluted RNA/DNA (fsc) from magnetic plate to elution plate
        for row in range(fsc):
            #pick up fresh tips from tip box 2
            left_pipette.pick_up_tip(tip_box_2[tipmatrix[0][row]])
            #elute 50uL purified RNA/DNA solution from full column(s) of sample to elution plate
            left_pipette.aspirate(elution_vol, mag_plate.rows()[0][row].bottom(1))
            left_pipette.dispense(elution_vol, elution_plate.rows()[0][row])
            left_pipette.blow_out(elution_plate.rows()[0][row])
            #discard tips
            left_pipette.drop_tip()

    #Transfer partial column of eluted RNA/DNA from magnetic plate to elution plate
    if x%8>0:
        #Pick up fresh tips from tip box 2 at y coordinate [pc_y]
        left_pipette.pick_up_tip(tip_box_2[tipmatrix[pc_y][pc_x]])
        #elute 50uL purified RNA/DNA solution from partially filled column of sample to elution plate
        left_pipette.aspirate(elution_vol, mag_plate.rows()[0][scp].bottom(1))
        left_pipette.dispense(elution_vol, elution_plate.rows()[0][scp])
        left_pipette.blow_out(elution_plate.rows()[0][scp])
        #discard tip(s)
        left_pipette.drop_tip()

    #Disengage magnet
    mag_module.disengage()
