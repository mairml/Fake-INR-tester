#!/usr/bin/env python
#Megan Mair 
import shelve
import time
import datetime
from tkinter import *
import ADC0832 #can't use pip... must use library file
import RPi.GPIO as GPIO

#This file has subsections for easy navigation.
###Table of contents:
#################################################
## BASIC NAVIGATION AND DISPLAY ELEMENTS
## INR TEST ELEMENTS
## HISTORY/DATA SAVE ELEMENTS
## QUALITY CHECK ELEMENTS
## RASPBERRY PI ELEMENTS
## MAIN SCRIPT


#################### BASIC NAVIGATION AND DISPLAY ELEMENTS ###########################
#Clears the display for a new 'page'
def clear_frame():
    list = window.grid_slaves()
    for l in list:
        l.destroy()

#primary home screen. Only appears at startup if the user is registered with Name
def base_script():
    clear_frame() #cleans up display
    lbl = Label(window, text="Welcome, " + name)
    lbl.grid(column=0, row=0) 
    btn = Button(window, text="New INR Test", command=enter_vals)
    btn2 = Button(window, text=name+"'s  History", command=history)
    btn3 = Button(window, text="INR QC", command=qc_calibrate)
    btn.grid(column=2, row=2)
    btn2.grid(column=2, row=3)
    btn3.grid(column=2,row=4)
    

#A button to take you back to the home screen 
#saves copy/paste trouble for navigation 
def home_button(display,x,y):
    back = Button(window, text=display, command=base_script)
    back.grid(column=x, row=y)

#################### INR TEST ELEMENTS ###########################

#Enter the MNPT/ISI values for INR test
def enter_vals():
    clear_frame()
    lbl_PT = Label(window, text="Enter the MNPT value for your test kit: ")
    lbl_PT.grid(row=0)
    lbl_ISI = Label(window, text="Enter the ISI value for your test kit: ")
    lbl_ISI.grid(row=1)
    PT = Entry(window,width=4)
    PT.grid(row=0, column=1)
    ISI = Entry(window,width=4)
    ISI.grid(row=1, column=1)
    PT_btn = Button(window,text="Enter Values")
    PT_btn['command']= lambda: test_values(PT,ISI) #check to see if values are floats
    PT_btn.grid(row=2, column=1)
    home_button("Cancel",1,3)

#Load the INR tester screen, prompt user ensure user is ready
def inr():
    clear_frame()
    lbl = Label(window, text="Prepare your sample. Press the button below to begin.")
    lbl.grid(column=0, row=0)
    home_button("Cancel",0,2)
    inr_btn = Button(window,text="Begin Read",command=lambda : inr_calc(PT,ISI))
    inr_btn.grid(column=0, row=1)

#Calculate the INR 
def inr_calc(PT,ISI): 
    clear_frame()
    #get photoresistor/laser settings
    photo_setup() 
    laser_setup()
	#Start counting prothrombin time
    start = time.perf_counter()
    inr_rasppi() #run the main raspberry pi modules
    #get time, turn off everything
    end = time.perf_counter() 
    laser_destroy()
    ADC0832.destroy()
    #Date/time of the read
    date = datetime.datetime.now()
    Patient = end - start #patient PT 
    INR = (Patient/PT)**ISI
    INR = round(INR,1) #round to one decimal
    #Print the data 
    clear_frame() 
    result = Label(window, text="The INR read was "+str(INR))
    result.grid(column=1, row=2)
    message= "For warfarin patients, an INR of 2-3, or higher is ideal."
    lbl = Label(window, text=message)
    lbl.grid(column=1, row=3)
    save_lbl = Label(window, text="Would you like to save this result to your history?")
    save_lbl.grid(column=1, row=4)
    save = Button(window,text="Save")
    save['command'] = lambda: save_data(date,INR,save)
    save.grid(column=1, row=5)
    home_button("Cancel session",1,6)
    

#Ensure the ISI and PT values are floats before continuting
def test_values(pt,isi):
    pt_val = pt.get()
    isi_val = isi.get()
    try:
        #we need these values later, so save them to global variables
        global PT
        global ISI 
        PT = float(pt_val) 
        ISI = float(isi_val)
        #Values are floats so we can continue
        clear_frame()
        #Ask user to confirm values 
        confirm = Label(window, text="Are these values ok?   MNPT: "+str(PT)+"\tSI: "+ str(ISI))
        confirm.grid(column=0, row=1)
        cont = Button(window,text="Yes, continue",command=inr)
        cont.grid(row=2,column=0)
        cancel = Button(window,text="No, go back",command=enter_vals)
        cancel.grid(row=3,column=0)
        
    except: #You did not enter a float or integer
        error = Label(window, text="Please enter integers/decimals.")
        error.grid(row=3, column=0)
        
##################### HISTORY/DATA SAVE ELEMENTS ###########################

#Save the result/datetime to the user dictionary
def save_data(date,INR,save):
    save.destroy()
    finish_save = Label(window,text="Finished saving.")
    finish_save.grid(column=1,row=5)
    time = date.strftime("%Y-%m-%d %H:%M:%S")
    time = str(time)
    data[time] = INR
    home_button("Go Back Home",1,6)

    
#Display user INR read history, if a history exists
def history():
    clear_frame()
    if len(data.keys())>1: #if the data has more than their name in the dictionary
        lbl = Label(window, text="User history for " + name)
        lbl.grid(column=0, row=0)
        #User might accumulate many results, so a scrollbar ensures results can be navigated
        textbox = Text(window, height=10, width=40) #textbox to hold history
        textbox.grid(column=0, row=1)
        scrl = Scrollbar(window, command=textbox.yview)
        textbox.config(yscrollcommand=scrl.set)
        scrl.grid(row=1, column=1,sticky='ns')
	#Get the history printed in order
        histories = sorted(data.keys(),reverse=True) #sort data by date 
        for event in histories:
            if event == "Name": #skip the name data
                pass
            else:
                textbox.insert(END, str(event) +"\t|\t"+ str(data[ event ])+"\n") #print history
        #Button to export the data to a file
        export_btn = Button(window,text="Save")
        export_btn['command'] = lambda: export(histories,export_btn)
        export_btn.grid(row=3,column=0)

    else: #if the user does not have any results yet 
        lbl = Label(window, text="No history to display yet.")
        lbl.grid(column=0, row=0)
    home_button("Go Back",0,4)

#Allow user to export their history to a csv file
#Useful to share the data with doctors, for example
def export(histories,export_btn):
    export_btn.destroy() #we don't need export button once it was pressed
    #Write to file
    outfile = open(name+"_INRdata.csv",'w')
    outfile.write("Date,INR_result\n")
    #print out all reads with most recent first
    #histories are sorted datetimes of each read
    for event in histories:
        if event == "Name":
            pass
        else:
            outfile.write(str(event) +","+ str(data[ event ])+"\n")
    outfile.close()
    #File save message
    lbl = Label(window, text="Successfully saved to " +name+"_INRdata.csv")
    lbl.grid(column=0, row=3)

#Button that saves the name upon startup of the program 
def name_save(txt):
    string = txt.get()
    data["Name"] = string
    global name #used later 
    name = data["Name"] #so program recognizes you can can start
    base_script()

################ QUALITY CHECK ELEMENTS ##################

#When you need to confirm light/photoresistor are working correctly
def qc_calibrate():
    clear_frame()
    lbl = Label(window, text="This mode is used to adjust light/sensor alignments")
    lbl.grid(column=0, row=0)
    #press button to start test
    cont = Button(window,text=" Adjust light/sensor alignments",command=lambda: tester_mode())
    cont.grid(row=1,column=0)
	#Directions:
    exit_lbl = Label(window, text="NOTE: Refer to terminal for photoresistor readings").grid(column=0, row=2)
    exit_lbl = Label(window, text="Press ctl+C to exit test. Window is not useable during test").grid(column=0, row=3)
    home_button("Go back home",0,4)

#Runs the test
def tester_mode():
    laser_setup()
    photo_setup()
    photo_test()

################## Raspberry Pi elements #########################

#The following block of code is adapted from the Sunfounder tutorial scripts
#First, set up modules:
def photo_setup():
    ADC0832.setup()

def laser_setup():
    GPIO.setmode(GPIO.BOARD) #Physical location of the pins 
    GPIO.setup(15, GPIO.OUT) #Output of laser
    GPIO.output(15, GPIO.HIGH) #laser Power

#Used for Quality Check - prints photoresistor values
#Program works best when the value is 0 with no obstruction
def photo_test():
    try:
        laser_loop() #turn on the laser
        time.sleep(0.1) #delay so laser turns on in time
        threshold = 50
        while True:
         #normalize light readings
            res = ADC0832.getResult() -80
            if res < 0: #0 = "a lot of light"
                res = 0
            if res > 100: #100 = "very dark"
                res = 100
            if res > threshold: #threshold for patient prothrombin time
                print("threshold reached")
            print('res = %d' % res) #photoresistor read to terminal
            time.sleep(0.2) #blink
    except KeyboardInterrupt:
	#Turn off everything 
        laser_destroy()
        ADC0832.destroy
        
#Turns on the laser
def laser_loop():
    GPIO.output(15, GPIO.HIGH) #led on

#Turns off the laser
def laser_destroy():
    GPIO.output(15, GPIO.LOW) #led off
    GPIO.cleanup() #Release resource

#Raspberry pi comonents for calculating INR
def inr_rasppi():
    #note: small delay to run code is okay
    #...it takes healthy blood about 12 seconds to clot
    laser_loop() #turn on the laser
    time.sleep(0.1) #delay so laser turns on in time for the photoresistor
    threshold = 50
    while True:
        light = ADC0832.getResult()-80
         #normalize light readings
        if light < 0: #0 = "a lot of light"
            light = 0
        if light > 100: #100 = "very dark"
            light = 100
        if light > threshold: #threshold for INR tester
            break
        time.sleep(0.05) #blinks every 0.05 seconds


################## Main Script #########################
#Establish window for GUI
window = Tk()
window.title("INR Tester")
window.geometry('400x400')

#Dictionary for saved user data
data = shelve.open('save')

#Try to load the startup page
try:
    global name
    name= data["Name"]
    base_script() #if the user exists, we can run the script
except: #Prompt user to enter name if they do not yet exist
    lbl = Label(window, text="Hello. Please type your name and click enter.")
    lbl.grid(column=0, row=0)
    txt = Entry(window,width=20)
    txt.grid(column=0, row=1)
    btn = Button(window, text="Enter", command=lambda: name_save(txt))
    btn.grid(column=0, row=2)

window.mainloop()
data.close() 
