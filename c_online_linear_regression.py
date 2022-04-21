import csv as csv
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from b_offline_data_processing import aggregate

def getData(verbose=False):
    # get master aggregate
    dfMasterCrashAgg = pd.read_pickle('program_data/master_crash_aggregate.pkl')
    
    # get sales data    
    dfSales = pd.read_pickle('program_data/sales_melted.pkl')
    
    if verbose:
	    print(dfMasterCrashAgg[:5])
	    print(dfSales[:5])

    return dfMasterCrashAgg, dfSales


def reaggregate( dfCrashAgg, groupBy=None):
    # If groupBy==None, then further aggregation is done, i.e. use agg level of dfCrashAgg.
    # Otherwise groupBy should be list of columns, e.g. ['MOD_YEAR', 'Make_ID', 'ACC_YEAR']

    if groupBy != None:
        df = aggregate( dfCrashAgg, groupBy=groupBy )
    else:
        df = dfCrashAgg
    
    return df

# df_sales:  
#      Make_Name Model_Name  Model_ID  Make_ID  Sales_Year  Sales
# 3        Acura        MDX       421       54        2005  57948
# 610      Acura        MDX       421       54        2006  54121
# 1217     Acura        MDX       421       54        2007  58606

def lookupSales(dfSales, Sales_Year, Make_ID, Model_ID, verbose=False ):
    '''
    Get closest Sales_Year sales.
    E.g. if 2000 is requested, 2005 sales is returned since that's the earliest sales data available.
    
    if Model_ID==None, then Make level sales will be returned.
    '''
    
    condition = []
    if Sales_Year != None:
        condition.append(f'Sales_Year>={Sales_Year}')
    if Make_ID != None:
        condition.append(f'Make_ID=={Make_ID}')
    if Model_ID != None:
        condition.append(f'Model_ID=={Model_ID}')
    
    condition = ' and '.join(condition)
    
        
    df = dfSales.query(condition)

    if df.empty:
        year, sales = None, None
    
    else:
        if Model_ID == None:
            df = df.groupby(['Make_ID','Sales_Year']) \
                    .agg(Sales=pd.NamedAgg(column='Sales', aggfunc=sum)) \
                    .reset_index()

        
        year, sales = df.Sales_Year.tolist()[0], df.Sales.tolist()[0]

                
    if verbose:
        print(condition)
#         print(df)
        print('year',year,'sales',sales)
        print()

    return year, sales

def linear_regress(dfCrashAgg, name, filterCondition, denom=None, showPlot=True):
    k = name
    v = dfCrashAgg.query(filterCondition)
    
    if v.empty:
        return None,None,None
    
    # start of linear regression calculation
    # create lists for year and fatalities to iterate through
    x_years = v['ACC_YEAR'].to_list()
    y_fatal = v['fatalities'].to_list()
    
    if denom != None:
        y_fatal = [y/(denom/1e6) for y in y_fatal]
        permillion = ' per million cars'
    else:
        permillion = ''
    
    yearOne = min(x_years)

    # find number of years of data
    num_years = len(x_years)

    # get regression coefficients for all data provided at least 2 years of data
    # otherwise coefficients = None and assign coefficients to coeff_all dictionary

    slope, intercept, initFatality = None, None, None
    if num_years > 1:
        slope, intercept = np.polyfit(x_years, y_fatal, 1)
        y_cal2 = []
        for m in range(len(x_years)):
            y_cal2.append(x_years[m]*slope + intercept)

    # print linear regression on top of scatter plot (if slope != None)
    if  slope != None:   
        initFatality = slope * yearOne + intercept
        
        if showPlot:
            
            fig,ax = plt.subplots()
            ax.scatter(x_years,y_fatal)
            ax.set_title(k)
            
            ax.plot(x_years, y_cal2, 'r') 
            ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:4.0f}'))
            ax.xaxis.set_label_text('accident year')
            ax.yaxis.set_label_text('annual fatality' + permillion)

            plt.show()        
            print(f'Slope {slope} intercept {intercept}')
            print(f'Initial fatality rate is {initFatality} per year')
    
    return slope, intercept, initFatality


def summarize_by_makeyear( dfCrashAgg, modelYrStart, modelYrEnd, makes_dict, dfSales=pd.DataFrame()
                         , showLinearRegress=False): 
    # **************************
    # BY MANUFACTURER **********
    # **************************
    # if dfSales is provided, it'll be used for normalization
    
    df = reaggregate(dfCrashAgg, groupBy=['MOD_YEAR', 'Make_ID', 'ACC_YEAR'])
    series={}    
    
    for makeName,ID in makes_dict.items():
        Make_ID  = ID['Make_ID']
        # Model_ID = ID['Model_ID']
        condition = f'Make_ID=={Make_ID}'  #' and Model_ID=={Model_ID}'
        
        x,y=[],[]
        for modelYear in range(modelYrStart, modelYrEnd + 1):
            
            if not dfSales.empty:
                year, sales = lookupSales(
                    dfSales, Sales_Year=modelYear, Make_ID=Make_ID, Model_ID=None, verbose=False)
                
                # sales could be None if not found
                if sales != None:
                    salesTitle = f' ({year} sales of {sales} vehicles)'
                    
            else:
                sales = None
                salesTitle = ''
            
            if dfSales.empty or sales!=None:
                _,_, initFatality = linear_regress(
                      dfCrashAgg      = df
                    , name            = f'{modelYear} {makeName} {salesTitle}'
                    , filterCondition = f'MOD_YEAR=={modelYear} and ACC_YEAR>=MOD_YEAR and '+condition
                    , denom           = sales
                    , showPlot        = showLinearRegress
                    )

                if initFatality != None:
                    x.append(modelYear)
                    y.append(initFatality)
        
        series[makeName] = [x,y]

    fig, ax = plt.subplots()

    i=1
    for makeName,data in series.items():
        if i<=10:
            fmt='solid'
        elif i<=20:
            fmt='dashed'
        else:
            fmt='dashdot'

        ax.plot(data[0], data[1], linestyle=fmt, label=makeName)
        i+=1
    
    if not dfSales.empty:
        permillion = ' per million cars'
    else:
        permillion = ''
    
    ax.set_xlabel('Model Year')  # Add an x-label to the axes.
    ax.set_ylabel('Annual Fatalities' + permillion)  # Add a y-label to the axes.
    ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:4.0f}'))
    ax.legend()
    plt.show()


def summarize_by_modelyear( dfCrashAgg, modelYrStart, modelYrEnd, models_dict, dfSales=pd.DataFrame()): 
    # if dfSales is provided, it'll be used for normalization
    
    series={}
    for modelName,ID in models_dict.items():
        Make_ID  = ID['Make_ID']
        Model_ID = ID['Model_ID']
        condition = f'Make_ID=={Make_ID} and Model_ID=={Model_ID}'
        
        x,y=[],[]
        for modelYear in range(modelYrStart, modelYrEnd + 1):
            
            if not dfSales.empty:
                year, sales = lookupSales(
                    dfSales, Sales_Year=modelYear, Make_ID=Make_ID, Model_ID=Model_ID, verbose=False)
                
                # sales could be None if not found
                if sales != None:
                    salesTitle = f' ({year} sales of {sales} vehicles)'
            else:
                sales = None
                salesTitle = ''
            
            if dfSales.empty or sales!=None:
                _,_, initFatality = linear_regress(
                      dfCrashAgg      = dfCrashAgg
                    , name            = f'{modelYear} {modelName} {salesTitle}'
                    , filterCondition = f'MOD_YEAR=={modelYear} and ACC_YEAR>=MOD_YEAR and '+condition
                    , denom           = sales
                    , showPlot        = (modelYear>=modelYrStart)
                    )

                if initFatality != None:
                    x.append(modelYear)
                    y.append(initFatality)
        
        series[modelName] = [x,y]

    fig, ax = plt.subplots()

    for modelName,data in series.items():
        ax.plot(data[0], data[1], label=modelName)
    
    if not dfSales.empty:
        permillion = ' per million cars'
    else:
        permillion = ''
    
    ax.set_xlabel('Model Year')  # Add an x-label to the axes.
    ax.set_ylabel('Annual Fatalities' + permillion)  # Add a y-label to the axes.
    ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:4.0f}'))
    ax.legend()
    plt.show()
    

if __name__ == '__main__':
    
    dfMasterCrashAgg, dfSales = getData(verbose=True)

    # test lookupSales
    lookupSales(dfSales, Sales_Year=2005, Make_ID=49, Model_ID=40, verbose=True) #camry
    lookupSales(dfSales, 2005, 49, None , True)  # toyota
    lookupSales(dfSales, 2005, 49, 4000 , True)  # non-existent model

    # test linear regression    
    linear_regress(dfMasterCrashAgg,'camry' , "MOD_YEAR==1999 and Make_ID==49 and Model_ID==40 ") 
    # with sales volume normalization
    year, sales = lookupSales(dfSales, Sales_Year=1999, Make_ID=49, Model_ID=40, verbose=True) #camry
    linear_regress(dfMasterCrashAgg,'camry' , "MOD_YEAR==1999 and Make_ID==49 and Model_ID==40", denom=sales) 


    #test re-aggregate & linear regression at Make level   
    dfCrashAggByMake = reaggregate(dfMasterCrashAgg, groupBy=['MOD_YEAR', 'Make_ID', 'ACC_YEAR'])
    linear_regress(dfCrashAggByMake,'toyota' , "MOD_YEAR==1999 and Make_ID==49 ")  
    # with sales volume normalization
    year, sales = lookupSales(dfSales, Sales_Year=1999, Make_ID=49, Model_ID=None, verbose=True) #camry
    linear_regress(dfCrashAggByMake,'toyota' , "MOD_YEAR==1999 and Make_ID==49 ", denom=sales)  

    # test summarize_by_makeyear (manufacturer)
    x = {}
    x['toyota'] = {'Make_ID':49}   
    x['ford'  ] = {'Make_ID':12}   
    modelYrStart=2004
    modelYrEnd  =2006
    
    summarize_by_makeyear( dfMasterCrashAgg, modelYrStart, modelYrEnd, makes_dict=x)    
    # with normalization
    summarize_by_makeyear( dfMasterCrashAgg, modelYrStart, modelYrEnd, makes_dict=x, dfSales=dfSales)


    # test summarize_by_modelyear (make & model)
    x = {}
    x['tacoma']        = {'Make_ID':49, 'Model_ID':472}   
    x['mustang']       = {'Make_ID':12, 'Model_ID':3  } 
    x['ford_f_series'] = {'Make_ID':12, 'Model_ID':481}   
    
    summarize_by_modelyear( dfMasterCrashAgg, modelYrStart, modelYrEnd, models_dict=x)
    # with normalization
    summarize_by_modelyear( dfMasterCrashAgg, modelYrStart, modelYrEnd, models_dict=x, dfSales=dfSales)


    

    







