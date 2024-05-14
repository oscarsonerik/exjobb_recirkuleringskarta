import streamlit as st; import numpy as np
import streamlit as st; import geopandas as gpd
import pandas as pd; import streamlit.components.v1 as stc
import matplotlib.pyplot as plt; import Calc_streamlit_8 as calc_last
import time; import math
from PIL import Image
st.set_page_config(page_title="Examensarbete", page_icon=":world_map:", layout="centered") #wide") # ":potable_water:"

# '''""""""'''
# Import the map to streamlit
# '''""""""'''

# This doesn't work..but it would be better
#path_to_html = 'index.html'
#with open(path_to_html, 'r', encoding="utf-8") as f:
#    html_data = f.read()
#st.components.v1.html(html_data, height=800, width=1200, scrolling=True)    
#https://docs.streamlit.io/1.30.0/library/components/components-api#stiframe
# To mirror the map on the streamlit window. The map needs to be online (website) by it self.
st.header("Recirkuleringskarta")
map = st.components.v1.iframe('http://127.0.0.1:5500/index.html#14/',height=500)
#https://oscarsonerik.github.io/endastindex/
#http://127.0.0.1:5500/index.html#14/
#"""""""""
# Input
#"""""""""
st.markdown('<hr style="border: 1px solid green;">', unsafe_allow_html=True)
st.subheader("Scenario för regnvattenanvändning")

arean = st.slider("Ange takarea för regnvatteninsamling [m²]", 
    min_value=0, max_value=1000,step=1)
avrinn_koeff = st.slider("Ange avrinningskoefficient", 
    min_value=0.7, max_value=0.9,step=0.01)
water_use = st.slider("Ange vattenbehov [l/d]", 
    min_value=0, max_value=1000,step=1)
wateruseday = water_use * 0.001 # liter --> m3
st.markdown('<hr style="border: 1px solid green;">', unsafe_allow_html=True)

@st.cache_data(show_spinner="Provar med olika tankstorlekar...") # Makes code alot faster, se link
#https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data
def calculate_efficiency(arean, avrinn_koeff, water_use):
    effi = []
    magsize = [i for i in range(101)]
    for size in magsize:
        svar = calc_last.GetData(size, water_use, arean, avrinn_koeff)
        upptag = svar[5]
        losten = svar[6]
        prec_M3 = svar[7]
        input_tank = svar[8]
        prec_mm = svar[9]
        avrinn_vol = svar[10]
        avg_year_365 = calc_last.Make365(upptag, losten, prec_M3, input_tank, prec_mm, avrinn_vol)
        procent_upptag = sum(avg_year_365[0]) / (wateruseday*365)
        effi.append(procent_upptag*100)
    return magsize, effi

magsize, effi = calculate_efficiency(arean, avrinn_koeff, water_use)

plt.figure(figsize=(10, 6))
plt.plot(magsize,effi)
plt.xlabel('Tankstorlek (m³)'); plt.ylabel('Behovstäckning i genomsnitt per år (%)')
plt.title('Andel av behovet som kommer täckas av regnvatten, beroende på tankstorlek')
plt.xticks(np.arange(0, 101, 10))
plt.yticks(np.arange(0, 101, 10))
st.pyplot(plt.gcf())

magazinsize = st.slider("Ange storlek på regnvattentank [m³]", 
    min_value=0, max_value=100,step=1)

    #"""""""""
    # Calculations
    #"""""""""

# Read the CSV file into a DataFrame
df = pd.read_csv('SMHI/SMHI_modified3.csv')
day = df['Dagar']
prec = df['Precip Medel']
temp = df['Temperature Medel']

# Call on GetData in Calculation.py file
svar = calc_last.GetData(magazinsize, water_use, arean, avrinn_koeff)
upptag = svar[5]; losten = svar[6]; prec_M3 = svar[7]; input_tank = svar[8]; prec_mm = svar[9]; avrinn_vol = svar[10]
# Call on Make365 to create an average year data set of the behavior from the simulation
avg_year_365 = calc_last.Make365(upptag, losten, prec_M3, input_tank, prec_mm, avrinn_vol)
# Call on MonthDisp to get data over how water is distributed over each month for avg year
month_avg = calc_last.MonthDisp(avg_year_365)


# __Start Checkers__
print("__Data mellan 2014-2022__")
print(f'Vattenmängd som kommer in i systemet {round(sum(svar[7]),2)}')
print(f'Rad 1. Vattenmängd använt från tanken: {round(svar[0],5)}')
print(f'Rad 2. Vattenmägd utanför tanken: {round(svar[1],5)}')
print(f'Rad 3. Vattemmängd kvar i tanken: {round(svar[2],5)}')
print(f'Rad 4. Vattenmängd kvar på taket: {round(svar[3],5)}')
total = svar[0]+svar[1]+svar[2]+svar[3]-(magazinsize*0.8)
print(f'Vattenmängd som kommer ut i systemet {round(total,2)}\n')
print("\t >> Tester för modellen 2014-2022<<")
if round(total,2) == round(sum(svar[7]),2):
    print("\t >> Modellen stämmer <<")
if svar[0] == sum(svar[5]):
    print("\t >> Appendar rätt upptagen vattenmängd <<")
if svar[1] == sum(svar[6]):
    print("\t >> Appendar rätt vattenförlust <<\n")
# plt.plot(svar[5]); plt.figure(2); plt.plot(svar[6]); plt.show(); plt.plot(svar[4]); plt.show()
print("__Skapar ett nytt dataset - avg_2014-2022 år__\n")
print(f"Vattenmängd som samlas in på takyta", round(sum(avg_year_365[2]),3), "m³/år.")
print(f'Önskad mängd regnvatten utnyttjad: {round((wateruseday*365),3)} m³/år. ')
print(f"Mängd regnvatten som inte får plats i vattentanken:", round(sum(avg_year_365[1]),3), " m³.\n")
print(f'Din input ger {round(sum(avg_year_365[0]),3)} m³ utnyttjad regnvatten per år.') # Blir inte exakt rätt då vi inte hämtar något vatten första dagen om det inte är någon nederbörd. First data dilemma.
#print("Mängd regnvatten kvar i tanken efter körning:", round((svar[2]/9),4), " m³.")
procent_upptag = sum(avg_year_365[0]) / (wateruseday*365)
print(f'Regnvatten står för {round(procent_upptag,4)*100} % av önskat behov under året.')
print(f'Mängd dricksvatten taget från kran {round((wateruseday*365) - sum(avg_year_365[0]),3)} m³/år.')
print('')
# __End Checkers__

#"""""""""
#Output
#"""""""""
# svar = [tot_h2o_use, water_out, volume_tank, snow_amount, vattentanknivå, apnd_upptag, apnd_water_out, prec_m3, apnd_water_in2tank, prec_mm, apnd_avrinn_volym]
st.image("images/inlluregnvatt3.png")
st.write("# Resultat")

st.write("Nederbördsvolym som faller på takyta:", round((sum(svar[9])*0.001*arean)/9,1), "m³/år.")
st.write("Avrinningsvolym som insamlas på takyta:", round(sum(svar[10])/9,1), "m³/år.")
st.write("Magasineringsvolym som samlas in i tanken", round(sum(svar[8])/9,1), "m³/år.")
st.write("Överflödig volym vatten", round(sum(svar[6])/9,1), "m³/år.")

# Plot genomsnittlga volymer
prec_temporery = np.array(month_avg[4])*0.001*arean
months = ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec']
antal_dagar_månad = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
x = months
x = np.arange(len(months))
y1 = prec_temporery
bar_width = 0.1
data = {'Nederbördsvolym': prec_temporery,
        'Avrinningsvolym': month_avg[5],
        'Magasineringssvolym': month_avg[3],
        'Överflödig volym': month_avg[2]}
dfen = pd.DataFrame(data, index=months)
ax = dfen.plot.bar(figsize=(10, 6))
plt.title('Genomsnittliga volymer')
plt.xlabel('Månad')
plt.ylabel('m³')
plt.xticks(x+bar_width, months)
plt.grid(False)
#plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.ylim(0, max(y1)+ max(y1) * 0.1)
plt.tight_layout()
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15))
st.pyplot(plt.gcf())

st.markdown('<hr style="border: 1px solid green;">', unsafe_allow_html=True)

st.write("Önskat återanvänt regnvatten till hushåll:", round((wateruseday*365),1), "m³/år.")
# st.markdown('<hr style="border: 1px solid green;">', unsafe_allow_html=True)
st.write("Volym som hämtas från regnvattentanken:", round(sum(avg_year_365[0]),1), "m³/år.")
#st.write("Mängd regnvatten som inte får plats i vattentanken:", round(sum(avg_year_365[1]),4), " m³.")
#st.write("Mängd regnvatten kvar i tanken efter körning:", round((svar[2]/9),4), " m³.")
st.write("Volym som behövs från annan vattenkälla:", round((wateruseday*365) - sum(avg_year_365[0]),1), " m³/år.")
procent_upptag = sum(avg_year_365[0]) / (wateruseday*365)
st.write("Andel av behovet som kommer täckas av regnvatten:", round((procent_upptag*100),1), " %.")
# Plot fördelning av vattenanvändning
antal_dagar_månad = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
wateruse_month = [i * wateruseday for i in antal_dagar_månad]
dricksvatten_mån = np.array(wateruse_month) - np.array(month_avg[1])
x = months
x = np.arange(len(months))
y1 = wateruse_month
bar_width = 0.1
data = {'Totalt vattenbehov': wateruse_month,
        'Regnvattenanvändning': month_avg[1],
        'Tillskottsbehov av vatten': dricksvatten_mån}
dfen = pd.DataFrame(data, index=months)
dfen.plot.bar(figsize=(10, 6))
plt.title('Fördelning av vattenanvändning')
plt.xlabel('Månad'); plt.ylabel('m³')
plt.xticks(x+bar_width, months)
#plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.ylim(0, max(y1)+ max(y1) * 0.1)
plt.tight_layout()
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15))
st.pyplot(plt.gcf())

st.markdown('<hr style="border: 1px solid green;">', unsafe_allow_html=True)

# Plot vattentankvolym
df_med_last_14 = pd.read_csv('SMHI/SMHI_2014_2020.csv',  delimiter=";", decimal=",")
years = df_med_last_14['År siffra']
days_per_year = 365
plt.figure(figsize=(10, 4))
plt.plot(svar[4], label = "Vattentankvolym")
tick_positions = [days_per_year * (i + 0.5) for i in range(len(years) // days_per_year)]
plt.xticks(
    tick_positions, #range(0, len(svar[4]), days_per_year),
    years[::days_per_year],  # Selecting only the first day of each year for labeling
    rotation=45  # Rotate labels for better readability
)
plt.xlabel('År'); plt.ylabel('m³')
plt.title('Volym vatten i tanken per dag mellan 2014-2022')
plt.ylim(0, (max(svar[4]) + max(svar[4])*0.05))
for i in range(0, len(svar[4]), days_per_year):
    plt.axvline(x=i, color='gray', linestyle='--', linewidth=0.5)  # Vertical line at the start of the year
    plt.axvline(x=i+days_per_year-1, color='gray', linestyle='--', linewidth=0.5)  # Vertical line at the end of the year
st.pyplot(plt.gcf())
st.markdown('<hr style="border: 1px solid green;">', unsafe_allow_html=True)


"""
Ta fram enheter av olika användarbehov
"""
st.write("Ange hur mycket vatten det går åt vid ett användningstillfälle, för att se vad vattnet kan räcka till.")
num_rows = 3
text = ["Toalettspolning", "Tvättvatten", "Bevattning"]
user_inputen = []
for i in range(num_rows):
    user_input = st.number_input(f"{i+1}: {text[i]} (liter/användningstillfälle)", min_value=0, value=0, step=1)
    if user_input < 0:
        user_input = 0
    user_inputen.append(user_input)
toa = user_inputen[0]; tvatt = user_inputen[1]; garden = user_inputen[2]
uttag_avg_month = np.array(month_avg[1])

@st.cache_data
def calculate_enheter(toa, tvatt, garden, uttag_avg_month):
    #arean, avrinn_koeff, water_use, magazinsize
    uttag_avg_month = uttag_avg_month * 1000
    Toalettspolning = uttag_avg_month / toa
    Tvättvatten = uttag_avg_month / tvatt
    Övrigt = uttag_avg_month / garden
    return Toalettspolning, Tvättvatten, Övrigt

# Call on "calculate_enheter" and plot result
Toalettspolning, Tvättvatten, Övrigt = calculate_enheter(toa, tvatt, garden, uttag_avg_month)
antal_dagar_månad = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
months = ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec']
x = months
x = np.arange(len(months))
y2 = month_avg[1]
bar_width = 0.1
data = {'Enbart toalettspolningar': Toalettspolning,
        'Enbart tvättar': Tvättvatten,
        'Enbart bevattningar': Övrigt,}
dfen = pd.DataFrame(data, index=months)
ax = dfen.plot.bar(figsize=(10, 6))
plt.title(f'Antal användningstillfällen som det totala vattenbehovet {water_use} (l/dygn) skulle kunna tillgodose')
plt.xlabel('Månad'); plt.ylabel('Antal användningstillfällen')
plt.xticks(x+bar_width, months)
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15))
plt.tight_layout()
st.pyplot(plt.gcf())


