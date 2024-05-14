import pandas as pd
import matplotlib.pyplot as plt
from statistics import mean
import numpy as np

'''
  Get Data. Is called from Streamlit.py
  - Reads csv.files
  - Load data into variables
  - Call on Water balance model
'''
def GetData(magazinsize, water_use, arean, avrinn_koeff):
  '''
  Read Csv.files
  '''
  df_365 = pd.read_csv('SMHI/SMHI_modified3.csv')
  df_med_last_14 = pd.read_csv('SMHI/SMHI_2014_2020.csv',  delimiter=";", decimal=",")
  # plt.plot(df_med_last_14['Temperatur'])
  #df_med_last_14 = pd.read_csv('SMHI/Piteå.csv', delimiter=';', decimal=",")
  # plt.figure()
  # plt.plot(df_med_last_14['Temperatur'])
  # plt.show()
  #df_med_last_14 = pd.read_csv('SMHI/SMHI_2014_2020_test.csv',  delimiter=";", decimal=",")
  df_med_last_14.insert(0, 'ID', range(len(df_med_last_14))) # Lägger till ID i första kolumnen
  """
  Load data into variable
  """
  roofarea = arean                                   # m2
  tanksize = magazinsize                                    # m3 
  wateruseday = water_use * 0.001   # Gör om l/day tll m3/day. (l = dm3 --> 1m3 = 1000dm3)
  ind = df_med_last_14["ID"]                       
  day = df_med_last_14['Dag siffra']               # Dag
  month = df_med_last_14['Månad siffra']           # Månad
  months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  year = df_med_last_14['År siffra']
  prec_mm = df_med_last_14['Nederbördsmängd']      # mm
  avrin_coef = avrinn_koeff
  prec_m = [i * avrin_coef * 0.001 for i in prec_mm]   # Gör om millimeter till meter
  prec_m3 = [i * roofarea for i in prec_m]             # Gör ny lista med area X nederbörd --> m3
  temp = df_med_last_14['Temperatur']                  # Celcius
  temp = [i for i in temp]
  volume_tank = tanksize * 0.8 # Make watertank to start with 80% of full volume
  tot_h2o_use = water_out = 0

  """
  Call on Water balance model and return
  """
  return WaterBalanceModel(ind, tanksize, volume_tank, tot_h2o_use, water_out, wateruseday, prec_m3, temp, roofarea, prec_mm, avrinn_koeff)


"""
  Water Balance Model.
"""
#plt.bar(ind,prec_m3); plt.show(); plt.plot(ind,temp); plt.show()
# Modellen tar in data för år 2014-2022 och kör den för att sedan returnera hur/var vattnet befinner sig under de 9 åren.
# Modellen tar in regnvatten först i tanken (början av dagen), sedan tar den upp vatten till huset(slutet av dagen)
# Antar att: vattentank fryser inte, snö på taket smälter efter HBV-model
def WaterBalanceModel(ind, tanksize, volume_tank, tot_h2o_use, water_out, wateruseday, prec_m3, temp, roofarea, prec_mm, avrinn_koeff):
  snow_amount = water_out_temp = 0
  apnd_upptag = [] # To track how much water is used from tank each day for 9 years
  apnd_water_out = [] # To track how much water to fits in water tank each day for 9 years
  apnd_water_in2tank = []
  vattentanknivå = []
  apnd_avrinn_volym = []
  for i in ind:
    # Minus degree
    if temp[i] < 0: # Kollar om det är snö eller regn
      # Påfyllnad
      snow_amount += prec_m3[i]      # Det är snö, bygger upp lager
      
      # Empty tank
      if wateruseday < volume_tank:      # Ska ändå kunna ta från tanken vid slutet av dagen vid minusgrader
        volume_tank -= wateruseday       # Tar bort vatten från tanken
        tot_h2o_use += wateruseday   # Fyller på countern i total användning av regnvatten
        apnd_upptag.append(wateruseday)
      else:
        apnd_upptag.append(volume_tank)
        tot_h2o_use += volume_tank
        volume_tank -= volume_tank           # Tömmer tanken på det vatten som finns kvar i tanken
      apnd_water_out.append(0) # Då inget vatten kommer in, inget vatten ut
      apnd_water_in2tank.append(0)
      apnd_avrinn_volym.append(0)
     
     # Plus degree
    else: 
      # Fyller på tanken
      if snow_amount != 0:
        day_melt = 0
        snowmelt_m3 = Snowmelt(temp[i], roofarea) # Hur mycket snö som smält den dagen [m3]
        #print(f'amount snowmelt {snowmelt_m3}')
        if snow_amount > snowmelt_m3: # Om det finns mer snö på lagret än vad som smältet är dagens snowmelt = snowmelt_m3
          day_melt = snowmelt_m3 * avrinn_koeff
          snow_amount -= snowmelt_m3 * avrinn_koeff # Tar bort den mängd som smälter från taklagret
        else:  # Om taklagret är mindre än det som kan smälta den dagen
          day_melt = snow_amount      # Dagens snösmältning är endast den mängd som finns på taket
          snow_amount = 0 
        avrinn_amount = day_melt + prec_m3[i]
      else:
        avrinn_amount = prec_m3[i]

      #apnd_water_in2tank.append(avrinn_amount) 
      apnd_avrinn_volym.append(avrinn_amount) 
      # Checkar om tanken får plats med allt vatten
      if tanksize > volume_tank + avrinn_amount:   
        volume_tank += avrinn_amount              # Beräknar volume_tankym, Antar att all snö smälter på en dag vid plusgrader
        apnd_water_out.append(0)  # Då inget vatten kommer in, inget vatten ut
        apnd_water_in2tank.append(avrinn_amount)
      else: # Om inte allt vatten får plats i tanken
        utrymme = tanksize - volume_tank
        water_out += avrinn_amount - utrymme 
        water_out_temp += avrinn_amount - utrymme
        apnd_water_out.append(water_out_temp)
        apnd_water_in2tank.append(utrymme)
        water_out_temp = 0
        volume_tank += utrymme         # Beräknar volume_tank
      
      # Empty tank
      if wateruseday < volume_tank:           # Ta vatten från tanken vid slutet av dagen vid plusgrader
        apnd_upptag.append(wateruseday)
        volume_tank -= wateruseday            # Tar bort vatten från tanken
        tot_h2o_use += wateruseday        # Fyller på countern i total användning av regnvatten
      else:
        apnd_upptag.append(volume_tank)
        tot_h2o_use += volume_tank  # Fyller på countern i total anvädning av regnvatten (det som finns kvar i tanken)
        volume_tank -= volume_tank      # Tömmer tanken på det vatten som finns kvar i tanken
    vattentanknivå.append(volume_tank)
  return (tot_h2o_use, water_out, volume_tank, snow_amount, vattentanknivå, apnd_upptag, apnd_water_out, prec_m3, apnd_water_in2tank, prec_mm, apnd_avrinn_volym)

'''
Empty Tank
'''
def EmptyTank():
  return 

'''
Snowmelt funciton
- Calculates the amount of snow that could melt on the roof for the day
'''
def Snowmelt(temp_dag, roofarea):
  Cm = 3.5                    # Koefficient
  Tt = 0                      # Tröskelvärde
  Ms = Cm * (temp_dag - Tt)   # mm   5 * 3,5 
  Ms = roofarea * Ms * 0.001  # m2 * mm * 0,001 = m3 --- 100 * (5 * 3,5 ) 
  return Ms                   # Returns in m3

'''
Make 365 avg year of watertanksystem
- Creates an average year of the 9 years that waas runned in the water balance model
'''
def Make365(upptag, losten, prec_m3, input_tank, prec_mm, avrinn_vol):
  yearss = 9
  values_per_year = 365
  avg_year_prec_m3 = []; avg_year_upptag = []
  avg_year_lost = []; avg_year_input_tank = []
  avg_year_prec_mm = []; avg_year_avrinn_vol = []
  for i in range(0, values_per_year): # Run through each day in a year
      sum_prec_m3 = sum_upptag = sum_lost = sum_input_tank = sum_prec_mm = sum_avrinn_vol = 0
      for j in range(0,9): # Run through each year
          index = (j * values_per_year) + (i)
          sum_prec_m3 += prec_m3[index]
          sum_upptag += upptag[index]
          sum_lost += losten[index]
          sum_input_tank += input_tank[index]
          sum_prec_mm += prec_mm[index]
          sum_avrinn_vol += avrinn_vol[index]
      average_prec_m3 = sum_prec_m3 / yearss
      average_upptag = sum_upptag / yearss
      average_lost = sum_lost / yearss
      average_input_tank = sum_input_tank / yearss
      average_prec_mm = sum_prec_mm / yearss
      average_avrinn_vol = sum_avrinn_vol / yearss

      avg_year_prec_m3.append(average_prec_m3)
      avg_year_upptag.append(average_upptag)
      avg_year_lost.append(average_lost)
      avg_year_input_tank.append(average_input_tank)
      avg_year_prec_mm.append(average_prec_mm)
      avg_year_avrinn_vol.append(average_avrinn_vol)
  return avg_year_upptag, avg_year_lost, avg_year_prec_m3, avg_year_input_tank, avg_year_prec_mm, avg_year_avrinn_vol


'''
Divide into month distribution
- Divides the average 365 year so that it is distributed over all month in a year.
'''
# OBS ! Ej samma ordning som för Make365
def MonthDisp(avg_year_365):
  # Create lists over the distribution over the month from the average year set.
  df_365 = pd.read_csv('SMHI/SMHI_modified3.csv')
  mån = df_365['Månad']
  #print(mån)
  antal_dagar_månad = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  my_365 = [i for i in range(1, 366)]
  mån_avg_prec = []; mån_avg_upptag = []
  mån_avg_lost = []; mån_avg_input_tank = []
  mån_avg_prec_mm = []; mån_avg_avrinn_vol = []
  mån_check = 1
  tempo_prec = tempo_up = tempo = tempo_intank = tempo_prec_mm =  tempo_avrinn_vol = 0
  for i in my_365:
      if mån[i-1] == mån_check:
          tempo_prec += avg_year_365[2][i-1]
          tempo_up += avg_year_365[0][i-1]
          tempo += avg_year_365[1][i-1]
          tempo_intank += avg_year_365[3][i-1]
          tempo_prec_mm += avg_year_365[4][i-1]
          tempo_avrinn_vol += avg_year_365[5][i-1]
          if i == 365:
              mån_avg_prec.append(tempo_prec)
              mån_avg_upptag.append(tempo_up)
              mån_avg_lost.append(tempo)
              mån_avg_input_tank.append(tempo_intank)
              mån_avg_prec_mm.append(tempo_prec_mm)
              mån_avg_avrinn_vol.append(tempo_avrinn_vol)
      else:
          mån_avg_prec.append(tempo_prec)
          mån_avg_upptag.append(tempo_up)
          mån_avg_lost.append(tempo)
          mån_avg_input_tank.append(tempo_intank)
          mån_avg_prec_mm.append(tempo_prec_mm)
          mån_avg_avrinn_vol.append(tempo_avrinn_vol)
          tempo_prec = tempo_up = tempo = tempo_intank = tempo_prec_mm = tempo_avrinn_vol = 0
          mån_check += 1
          # Måste nu fixa temporary, för annars missar vi en iteration då vi går in i else state.
          tempo_prec += avg_year_365[2][i-1]
          tempo_up += avg_year_365[0][i-1]
          tempo += avg_year_365[1][i-1]
          tempo_intank += avg_year_365[3][i-1]
          tempo_prec_mm += avg_year_365[4][i-1]
          tempo_avrinn_vol += avg_year_365[5][i-1]
  mån_avg = []
  mån_avg.append(mån_avg_prec)
  mån_avg.append(mån_avg_upptag)
  mån_avg.append(mån_avg_lost)
  mån_avg.append(mån_avg_input_tank)
  mån_avg.append(mån_avg_prec_mm)
  mån_avg.append(mån_avg_avrinn_vol)
  #print(mån_avg)
  return mån_avg







'''
If we just want to run this script
'''
if __name__ == "__main__":

  arean = 100
  avrinn_koeff = 0.8
  water_use = 200
  magazinsize = 7
  svar = GetData(magazinsize, water_use, arean, avrinn_koeff)
  print(f'hej')
  print("__Data mellan 2014-2022__")
  print(f'Vattenmängd som kommer in i systemet {round(sum(svar[7]),2)}')
  print(f'Rad 1. Vattenmängd använt från tanken: {round(svar[0],5)}')
  print(f'Rad 2. Vattenmägd utanför tanken: {round(svar[1],5)}')
  print(f'Rad 3. Vattemmängd kvar i tanken: {round(svar[2],5)}')
  print(f'Rad 4. Vattenmängd kvar på taket: {round(svar[3],5)}')
  total = svar[0]+svar[1]+svar[2]+svar[3]-(magazinsize*0.8) # Behöver dra bort den mängd vatten som redan är i vattentanken
  print(f'Vattenmängd som kommer ut i systemet {round(total,2)}\n')
  print("\t >> Tester för modellen 2014-2022<<")
  if round(total,2) == round(sum(svar[7]),2):
      print("\t >> Modellen stämmer <<")
  if svar[0] == sum(svar[5]):
      print("\t >> Appendar rätt upptagen vattenmängd <<")
  if svar[1] == sum(svar[6]):
      print("\t >> Appendar rätt vattenförlust <<\n")
  # plt.plot(svar[5]); plt.figure(2); plt.plot(svar[6]); plt.show()
  #plt.plot(svar[4]); plt.show()
  #print(svar[4][:5])
  # Create a new data-set --> an average year based on the model run. New data-set created by Make365. 
  print("__Skapar ett nytt dataset - avg_2014-2022 år__\n")
  upptag = svar[5]
  losten = svar[6]
  prec_M3 = svar[7]
  input_tank = svar[8]
  prec_mm = svar[9]
  avrinn_vol = svar[10]
  avg_year_365 = Make365(upptag, losten, prec_M3, input_tank, prec_mm, avrinn_vol)
  wateruseday = water_use * 0.001
  print(f"Vattenmängd som samlas in på takyta", round(sum(avg_year_365[2]),3), "m³/år.")
  print(f'Önskad mängd regnvatten utnyttjad: {round((wateruseday*365),3)} m³/år. ')
  print(f"Mängd regnvatten som inte får plats i vattentanken:", round(sum(avg_year_365[1]),3), " m³.\n")
  print(f'Din input ger {round(sum(avg_year_365[0]),3)} m³ utnyttjad regnvatten per år.') # Blir inte exakt rätt då vi inte hämtar något vatten första dagen om det inte är någon nederbörd. First data dilemma.
  #print("Mängd regnvatten kvar i tanken efter körning:", round((svar[2]/9),4), " m³.")
  procent_upptag = sum(avg_year_365[0]) / (wateruseday*365)
  print(f'Regnvatten står för {round(procent_upptag,4)*100} % av önskat behov under året.')
  print(f'Mängd dricksvatten taget från kran {round((wateruseday*365) - sum(avg_year_365[0]),3)} m³/år.')
  # plt.figure()
  # plt.plot(svar[7])
  # plt.show()
  # plt.figure()
  # plt.plot(svar[8])
  # plt.show()
  month_avg = MonthDisp(avg_year_365)

# ____________

  # svar = (tot_h2o_use, water_out, volume_tank, snow_amount, vattentanknivå, apnd_upptag, apnd_water_out, prec_m3, apnd_water_in2tank, prec_mm, apnd_avrinn_volym)  
  # Creating the boxplot
  df_med_last_14 = pd.read_csv('SMHI/SMHI_2014_2020.csv',  delimiter=";", decimal=",")
  years = df_med_last_14['År siffra']
  days_per_year = 365
  tick_positions = [days_per_year * (i + 0.5) for i in range(len(years) // days_per_year)]
  for i in range(0, len(svar[4]), days_per_year):
    plt.axvline(x=i, color='gray', linestyle='--', linewidth=0.5)
    plt.axvline(x=i+days_per_year, color='gray', linestyle='--', linewidth=0.5)
  tick_positions = [days_per_year * (i + 0.5) for i in range(len(years) // days_per_year)]
  plt.xticks(
      tick_positions, #range(0, len(svar[4]), days_per_year),
      years[::days_per_year],  # Selecting only the first day of each year for labeling
      rotation=45  # Rotate labels for better readability
  )
  plt.plot(svar[4], label="Vattentanknivå"); plt.plot(svar[5], label="Vattenuttag"); plt.plot(svar[6], label="Överflödigt vatten"); plt.plot(svar[8], label="Magasineringsvatten"); plt.plot(svar[10], label="Avrinningsvatten") #; plt.show()
  plt.ylim(-0.1); plt.title("Vattenbalansmodell"); plt.ylabel('m³'); plt.legend()

# ____________

    # Plot genomsnittlga volymer
  prec_temporery = np.array(month_avg[4])*0.001*arean
  months = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']
  antal_dagar_månad = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  x = months
  x = np.arange(len(months))
  y1 = prec_temporery
  bar_width = 0.1
  data = {'Nederbördsvolym': prec_temporery,
          'Magasineringssvolym': month_avg[3],
          'Överflödig volym': month_avg[2]}
  dfen = pd.DataFrame(data, index=months)
  ax = dfen.plot.bar(figsize=(10, 6))
  plt.title('Genomsnittliga volymer')
  plt.xlabel('Månad')
  plt.ylabel('m³')
  plt.xticks(x+bar_width, months)
  plt.grid(False)
  plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
  plt.ylim(0, max(y1)+ max(y1) * 0.1)
  plt.tight_layout()

# ____________
  
  # svar = (tot_h2o_use, water_out, volume_tank, snow_amount, vattentanknivå, apnd_upptag, apnd_water_out, prec_m3, apnd_water_in2tank, prec_mm, apnd_avrinn_volym)
  df_365 = pd.read_csv('SMHI/SMHI_modified3.csv')
  data_ned = svar[9]
  data_ned = np.array(data_ned)*0.001*arean
  data_in2tank = svar[8]
  data_overflow = svar[6]
  data_upptag = svar[5]
  data_avrinn_vol = svar[10]
  mån = df_365['Månad']
  #print(mån)
  months_dataset = [[] for _ in range(12)]
  overflow_dataset = [[] for _ in range(12)]
  prec_dataset = [[] for _ in range(12)]
  upptag_dataset = [[] for _ in range(12)]
  avrinn_vol_dataset = [[] for _ in range(12)]
  #print(months_dataset)
  tempo_ned = tempovalue = tempo_overflow = tempo_upptag = tempo_avrinn_vol = start_indexet = 0
  prev_month = 0
  extra = 0
  # Iterate over each year
  for i in range(9):
    # Initialize a list to store the sum of each month for the current year
    for day, month_value in enumerate(mån):
      # Get the index of the current day within the big dataset
      index = day + extra
      # Calculate the month based on the day index
      month = month_value - 1 
      if month != prev_month:
        prec_dataset[prev_month].append(tempo_ned)
        months_dataset[prev_month].append(tempovalue)
        overflow_dataset[prev_month].append(tempo_overflow)
        upptag_dataset[prev_month].append(tempo_upptag)
        avrinn_vol_dataset[prev_month].append(tempo_avrinn_vol)
        tempo_ned = tempovalue = tempo_overflow = tempo_upptag = tempo_avrinn_vol = 0
        prev_month = month
      # Add the data for the current row to the sum of its corresponding month
      tempo_ned += data_ned[index]
      tempovalue += data_in2tank[index]
      tempo_overflow += data_overflow[index]
      tempo_upptag += data_upptag[index]
      tempo_avrinn_vol += data_avrinn_vol[index]

    prec_dataset[prev_month].append(tempo_ned)
    months_dataset[prev_month].append(tempovalue)
    overflow_dataset[prev_month].append(tempo_overflow)
    upptag_dataset[prev_month].append(tempo_upptag)
    avrinn_vol_dataset[prev_month].append(tempo_avrinn_vol)
    tempo_ned = tempovalue = tempo_overflow = tempo_upptag = tempo_avrinn_vol = prev_month = 0
    extra += 365
   # Skapa en boxplot för varje månad
  plt.figure(figsize=(10, 6))
  positions = np.arange(1, 13)
  flierprops1 = dict(marker='o', markerfacecolor='lightblue', markersize=4, linestyle='-', markeredgecolor='black')
  flierprops2 = dict(marker='o', markerfacecolor='#FFDAB9', markersize=4, linestyle='none', markeredgecolor='black')
  flierprops3 = dict(marker='o', markerfacecolor='lightgreen', markersize=4, linestyle='none', markeredgecolor='black')
  flierprops4 = dict(marker='o', markerfacecolor='lightcoral', markersize=4, linestyle=':', markeredgecolor='black')

  prec_box = plt.boxplot(prec_dataset, positions = positions - 0.15, widths=0.1, patch_artist=True, boxprops=dict(facecolor='lightblue', color='black'), medianprops=dict(color='black'), flierprops=flierprops1)
  
  avrinn_vol_box = plt.boxplot(avrinn_vol_dataset, positions= positions - 0.05, widths=0.1, patch_artist=True, boxprops=dict(facecolor='#FFDAB9', color='black'), medianprops=dict(color='black'), flierprops=flierprops2)

  twotank_box = plt.boxplot(months_dataset, positions= positions + 0.05, widths=0.1, patch_artist=True, boxprops=dict(facecolor='lightgreen', color='black'), medianprops=dict(color='black'), flierprops=flierprops3)

  overflow_box = plt.boxplot(overflow_dataset, positions= positions + 0.15, widths=0.1, patch_artist=True, boxprops=dict(facecolor='lightcoral', color='black'), medianprops=dict(color='black'), flierprops=flierprops4)
  plt.xticks(np.arange(1, 13), ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'])
  plt.title('Fördelning vattenvolymer')
  plt.ylabel('m³')
  plt.grid(True)
  plt.legend([prec_box['boxes'][0], avrinn_vol_box['boxes'][0], twotank_box['boxes'][0], overflow_box['boxes'][0]], ['Nederbördsvolym', 'Avrinningsvolym', 'Magasineringsvolym', 'Överflödig volym'], loc='upper center', bbox_to_anchor=(0.5, -0.07), fancybox=True, shadow=True, ncol=4)
  print("\n")

# ____________

  '''
  Under utveckling
  '''
  # Typ av vatten och tillgång
  # antal_dagar_månad = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  # wateruse_per_month = [wateruseday * days for days in antal_dagar_månad]
  # wateruse_month = [[wateruse_per_month[i]] * 9 for i in range(12)]
  # print(wateruse_month)
  # dricksvatten_mån = np.array(wateruse_month) - np.array(upptag_dataset)
  # print(len(upptag_dataset))
  # print(len(dricksvatten_mån))
  # print(np.round(dricksvatten_mån, decimals=2))
  # data = [upptag_dataset, dricksvatten_mån]
  # plt.figure(figsize=(10,6))
  # positions1 = np.arange(1, 13)
  # positions2 = np.arange(1, 13) + 0.2
  # plt.bar(np.arange(1, 13)-0.2, wateruse_per_month, width=0.2, label='Water Usage', color='lightblue')
  # plt.boxplot(upptag_dataset, positions=positions1, widths=0.2, patch_artist=True, boxprops=dict(facecolor='#FFDAB9', color='black'), medianprops=dict(color='black'))
  # plt.boxplot(dricksvatten_mån.T, positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor='lightgreen', color='black'), medianprops=dict(color='black')) # .T för att göra np.array transpose/transponat
  # plt.xticks(np.arange(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'])
  # plt.xlabel('Månad')
  # plt.title("Fördelning av vattenanvädning")
  '''
  Under utveckling
  '''
# ____________

  # För return från avg_year_365
  # avg_year_365 = avg_year_upptag, avg_year_lost, avg_year_prec_m3, avg_year_input_tank, avg_year_prec_mm
  # antal_dagar_månad = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  # # Ditt dataset med 365 dagar
  # dataset_365_dagar = avg_year_365[3]  # Exempeldata
  # # Skapa en lista med 12 listor, en för varje månad
  # delade_listor = []
  # start_index = 0
  # for antal_dagar in antal_dagar_månad:
  #     delade_listor.append(dataset_365_dagar[start_index:start_index + antal_dagar])
  #     start_index += antal_dagar
  # plt.figure(figsize=(10, 6))
  # plt.boxplot(delade_listor)
  # # Anpassa x-axeln för att visa månaderna
  # plt.xticks(np.arange(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'])
  # plt.title('Magasineringsvolym')
  # plt.xlabel('Månad')
  # plt.ylabel('m³')
  # plt.grid(True)
  # plt.tight_layout()
  # print(sum(dataset_365_dagar[:31]))
  # print("\n")

# ____________

  # Punkter för varje månad
  # antal_dagar_månad = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  # # Ditt dataset med 365 dagar
  # dataset_365_dagar = avg_year_365[3]  # Exempeldata
  # # Skapa en lista med 12 listor, en för varje månad
  # delade_listor = []
  # start_index = 0
  # for antal_dagar in antal_dagar_månad:
  #     delade_listor.append(dataset_365_dagar[start_index:start_index + antal_dagar])
  #     start_index += antal_dagar
  # # Skapa en lista med månader för x-axeln
  # months = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']
  # # Plotta punkter för varje månad
  # plt.figure(figsize=(10, 6))
  # for i, månadslista in enumerate(delade_listor):
  #     x_values = [i+1] * len(månadslista)  # x-koordinater (månader)
  #     plt.scatter(x_values, månadslista, label=f'Månad {i+1}')
  # # Anpassa x-axeln för att visa månaderna
  # plt.xticks(np.arange(1, 13), months)
  # plt.title('Punktplott för varje månad')
  # plt.xlabel('Månad'); plt.ylabel('Data')
  # plt.legend(); plt.grid(True)
  # plt.tight_layout()

# ____________
  
  # svar = (tot_h2o_use, water_out[1], volume_tank, snow_amount[3], vattentanknivå, apnd_upptag[5], apnd_water_out, prec_m3[7], apnd_water_in2tank, prec_mm[9], apnd_avrinn_volym)
  dataset1 = svar[4]
  yearlylist1 = [dataset1[i*365:i*365+365] for i in range(9)]
  dataset2 = svar[7]
  yearlylist2 = [dataset2[i*365:i*365+365] for i in range(9)]
  # print(svar[8])
  # print("\n")
  # print(yearlylist)  
  plt.figure(figsize=(10, 6))
  plt.boxplot(yearlylist1, widths=0.2, patch_artist=True, boxprops=dict(facecolor='lightblue', color='black'), medianprops=dict(color='black'))
  #plt.boxplot(yearlylist2, positions=[i-0.1 for i in range(1, 10)], widths=0.2, patch_artist=True, boxprops=dict(facecolor='lightcoral', color='red'))
  plt.xticks(range(1, 10), ['2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022'])
  plt.xlabel('År'); plt.ylabel('m³')
  plt.title('Fördelning volym vatten i tanken')
  plt.tight_layout()
  plt.show()

  for sublist in svar:
    if isinstance(sublist, list):  
      print("längden för listan:", len(sublist))
    else:
       print("Not a list:", sublist)
  
  
  
  print('')
