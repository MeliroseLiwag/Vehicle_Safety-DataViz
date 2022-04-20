import csv as csv

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plot

# from IPython.display import display
#todo: age of vehicle column
#todo:addstate,state#,yearofaccidenttoeachcsvNHTSA,case#

dir = 'NHTSA-FARS-download/'
usecols = ['MOD_YEAR', 'MAKE', 'MODEL', 'DEATHS']
startYR, endYR = 2005, 2015
nrows = None        #set to None to read all

df_final = None # pd.DataFrame(columns=usecols)
for year in list(range(startYR, endYR + 1)):

    print('reading', year)
    df = pd.read_csv(f'{dir}vehicle{year}.csv', encoding='latin1', header=0, usecols=usecols
                     , nrows=nrows)  #.astype(str)      # , dtype={'DEATHS':'int32'}
    df['YEAR'] = year
    # print(df[:5])

    if df_final is None:
        df_final = df
    else:
        df_final = pd.concat([df_final, df], ignore_index=True)

print('aggregating...')
# print('** df_final **')
# print(df_final.info())

df_agg = df_final.groupby(['MOD_YEAR', 'MAKE', 'MODEL','YEAR']) \
    .agg(fatalities=pd.NamedAgg(column='DEATHS', aggfunc=sum)) \
    .reset_index()

print(df_agg[:20])

# sample = df_agg[(df_agg.MAKE=='49') & (df_agg.MODEL=='40')  & (df_agg.MOD_YEAR=='1999')]
# print(sample[:5])

x={}
x['camry'] = df_agg.query("MAKE==49 and MODEL==40 and MOD_YEAR==1999")  #camry
x['tacoma'] = df_agg.query("MAKE==49 and MODEL==472 and MOD_YEAR==1999")  #tacoma
x['mustang'] = df_agg.query("MAKE==12 and MODEL==3 and MOD_YEAR==1999")
x['ford_f_series'] = df_agg.query("MAKE==12 and MODEL==481 and MOD_YEAR==1999")
x['crown_vicoria'] = df_agg.query("MAKE==12 and MODEL==16 and MOD_YEAR==1999")


d_avg_fatal = {}
coeff_all = {}
for k,v in x.items():
    print(f'*** {k} ***\n', v)
    ax = v.plot.scatter(x='YEAR',y='fatalities',label=k)
    plot.title(k)
    ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:4.0f}'))
    plot.show()

    # start of linear regression calculation
    # create lists for year and fatalities to iterate through
    x_years = v['YEAR'].to_list()
    y_fatal = v['fatalities'].to_list()
    
    # find number of years of data
    num_years = len(x_years)
    
    # get regression coefficients for all data provided at least 2 years of data
    # otherwise coefficients = None and assign coefficients to coeff_all dictionary
    if num_years > 1:
        slope, intercept = np.polyfit(x_years, y_fatal, 1)
        coeff_all[k] = {'slope': slope, 'intercept': intercept}
        y_cal2 = []
        for m in range(len(x_years)):
            y_cal2.append(x_years[m]*coeff_all[k]['slope'] + coeff_all[k]['intercept'])
        #print(y_cal2)       
    else:
        coeff_all[k] = {'slope': None, 'intercept': None}

    # print linear regression on top of scatter plot (if slope != None)
    if  coeff_all[k]['slope'] != None:   
        ax2 = v.plot.scatter(x='YEAR',y='fatalities',label=k)
        plot.title(k)
        ax2.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:4.0f}'))
        plot.plot(x_years, y_cal2, 'r')
        plot.show()
    
    
    # set flag for case of zero fatalities for all years
    flag = 0
    # iterate through years to find first year with non-zero fatalities (assume that this model
    # did not exist in prior years) and break for year of first non-zero fatalities
    for i in range(len(x_years)):
        if y_fatal[i] != 0:
            flag = 1
            break

    # set average fatalities - if zero, average fatalities = zero
    if flag == 0:
        d_avg_fatal[k] = 0

    # do linear regression if two or more years of data, otherwise, fatalities is
    # set equal to the only year of data
    else:
        # check years of non-zero fatalties after the first year of non-zero fatalities
        # if i+3 > num_years-1 then only one or two years of non-zero fatalities
        if num_years  > i+3:
            end = i + 3
        else:
            end = num_years 
        # set x and y data for polyfit function   
        yf = y_fatal[i:end]
        xy = x_years[i:end]
        # check length of years - if one year only, set the average fatality to that year
        # otherwise, do polyfit and then calculate the years
        if len(xy) == 1:
            d_avg_fatal[k] = yf[i]
        else:
            # reference:  https://www.educba.com/numpy-polyfit/
            coeff = np.polyfit(xy, yf, 1)
            y_cal = np.poly1d(coeff)
            numerator = 0
            for j in range(len(xy)):
                addition = y_cal(xy[j])
                #print("addition is ", addition)
                numerator += addition

            average = numerator/len(xy)
            #print("average calculated is ", average)
            d_avg_fatal[k] = average

        print(f"average fatality rate per year over first three years is {d_avg_fatal[k]}, coeff {coeff}")
        print("  ")
           
       
df_agg2 = df_final.groupby(['MOD_YEAR', 'MAKE', 'YEAR']) \
    .agg(fatalities=pd.NamedAgg(column='DEATHS', aggfunc=sum)) \
    .reset_index()

print(df_agg2[:20])       

x2={}
x2['toyota'] = df_agg2.query("MAKE==49 and MOD_YEAR==1999")  #camry
x2['ford'] = df_agg2.query("MAKE==12 and MOD_YEAR==1999")

d_avg_fatal_make = {}
for k,v in x2.items():
    print(f'*** {k} ***\n', v)    
    ax = v.plot.scatter(x='YEAR',y='fatalities',label=k)
    plot.title(k)
    ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:4.0f}'))
    plot.show()

    # start of linear regression calculation
    # create lists for year and fatalities to iterate through
    x_years2 = v['YEAR'].to_list()
    y_fatal2 = v['fatalities'].to_list()
    # find number of years of data
    num_years = len(x_years2)
    # set flag for case of zero fatalities for all years
    flag = 0
    # iterate through years to find first non-zero fatalities (assume that this model
    # did not exist in prior years) and break for year of first non-zero fatalities
    for i in range(len(x_years2)):
        if y_fatal2[i] != 0:
            flag = 1
            break

    # set average fatalities - if zero, average fatalities = zero
    if flag == 0:
        d_avg_fatal_make[k] = 0

    # do linear regression if two or more years of data, otherwise, fatalities is
    # set equal to the only year of data
    else:
        # check years of non-zero fatalties after the first year of non-zero fatalities
        # if i+3 > num_years-1 then only one or two years of non-zero fatalities
        if num_years  > i+3:
            end = i + 3
        else:
            end = num_years 
        # set x and y data for polyfit function   
        yf = y_fatal2[i:end]
        xy = x_years2[i:end]
        # check length of years - if one year only, set the average fatality to that year
        # otherwise, do polyfit and then calculate the years
        if len(xy) == 1:
            d_avg_fatal_make[k] = yf[i]
        else:
            # reference:  https://www.educba.com/numpy-polyfit/
            coeff = np.polyfit(xy, yf, 1)
            y_cal = np.poly1d(coeff)
            numerator = 0
            for j in range(len(xy)):
                addition = y_cal(xy[j])
                #print("addition is ", addition)
                numerator += addition

            average = numerator/len(xy)
            #print("average calculated is ", average)
            d_avg_fatal_make[k] = average

        print(f"average fatality rate per year over first three years is {d_avg_fatal_make[k]}, coeff {coeff}")
        print("  ")

'''
#easily creates a name list for pulling in csv filenames
def file_namer(startYR, endYR, name, dir=''):
    #number range in list format
    #name = string name of file
    name_list = []
    for year in list(range(startYR, endYR+1)):
        name_list.append( dir + name + str(year) + '.csv')
    return name_list

#creates a set of a column for future filtering
def get_setlist(filenames, col):
    #filenames = a list of filenames/.CSVs
    #col = the column name to create a set out of
    df_final = pd.DataFrame(columns=usecols)
    for file in filenames:
        print('reading', file)
        df = pd.read_csv(file, encoding='latin1', header=0, usecols=usecols
                         , nrows=1000 ).astype(str)

        df_final = pd.concat([df_final, df], ignore_index=True)
    return set(df_final[col])




makemod_filenames = file_namer(2014, 2016, 'vehicle', dir)

make_set = get_setlist(makemod_filenames, col='MAKE')
print(make_set)
mod_set = get_setlist(makemod_filenames, col='MODEL')
print(mod_set)

def Load_NHTSA_Data(filenames):

    old_cols = ['MOD_YEAR', 'MAKENAME', 'MAK_MODNAME', 'BODY_TYP', 'DEATHS']
    df_final = pd.DataFrame(columns=['Year', 'Make', 'Model', 'BODY_TYP'])
    # read through each filename in filenames
    for file in filenames:
        df = pd.read_csv(file, encoding='latin1', header=0, usecols=old_cols).astype(str)
        # print(df.isna().sum())
        df.rename(columns={"MOD_YEAR": "Year",
                           "MAKENAME": "Make",
                           "MAK_MODNAME": "Model",
                           }, inplace=True)

        df['DEATHS'] = df["DEATHS"].astype('int32') #Convert deaths col to int
        df = df[~df['Make'].str.contains("Unknown")] # filter out Unknown rows
        df = df[df['DEATHS'] > 0] #Filter for fatalities only
        df.drop('DEATHS', axis=1, inplace=True) #drop death column

        for i, v in enumerate(df["Model"]):
            print(i)
            print(v)
            #if i in make_set:
            #    df["Model"]
            break

        # get model names separated into a new df
        df["Model"] = df["Model"].str.replace(r'/', ' ')

        #df_makes = df["Model"].str.split(" ", n=2, expand=True)
        #print(df_makes.columns.tolist())
        #df_makes.drop(0, axis=1, inplace=True)
        #print(df_makes)
        #df_makes_select = df_makes[[-1]].agg('-'.join, axis=1)
        #print(df_makes_select[0:10])
        # create new model col in main df
        #df['Model_1'] = df_makes[1]

        # kill white spaces across all cols
        df = df.apply(lambda x: x.str.strip())

        # deal with possible NAs
        df['Year'].fillna('0', inplace=True)
        df.fillna('unknown', inplace=True)
        #df['Model'].fillna('unknown', inplace=True)
        # create final df by concating the old with the new trimmed df
        df_final = pd.concat([df_final, df], ignore_index=True)

    #df_final.drop_duplicates(inplace=True, ignore_index=True)
    return df_final

# list file names to concat into one df
filenames = file_namer(2016, 2020, 'Vehicle')
NHTSA_Data = Load_NHTSA_Data(filenames)
#print(NHTSA_Data[0:10])
compression_opts = dict(method='zip', archive_name='NHTSA.csv')

NHTSA_Data.to_csv('NHTSA.zip', index=False, compression=compression_opts)
'''


# def Load_Sales_Data(filename):
#     keep_cols = ['Make', 'Model', '2016', '2017', '2018', '2019', '2020']
#     df = pd.read_csv('marklines2016-2021.csv', encoding='latin1', header=0, usecols=keep_cols).astype(str)
#     return df
#
#
#
#
#
#
# #sales_data = Load_Sales_Data('marklines2016-2021.csv')
# #print(sales_data)
#
# #final_df = pd.merge(NHTSA_Data, sales_data, on=['Make'])
# #print(final_df)
# #print(len(final_df))
# compression_opts = dict(method='zip', archive_name='NHTSA-SalesData_MAKE.csv')
#
# #final_df.to_csv('NHTSA-SalesData_MAKE.zip', index=False, compression=compression_opts)
