#%% [markdown]

## Introduction

#This is a very basic portfolio optimizer. Based on a list of stocks and their monthly return for during the past 5 years, the optimization will minimize the risks (standard deviation in this case) while achieving a required return.


#Again, this is a very basic and naive optimizer, more feature will be added on as I learned more



#Stock data are gather using the yfinance library
#Optimization is performed using cvxpy library



#%% [markdown]
### 0. Import Libraries

#%% 
import cvxpy as cp
import numpy as np  
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

print ("finished loading libraries")

#%% [markdown]
### 1. Prepare Helper function


#%% 

def load_symbol(symbol_list, period = "5y"):
    """ Given a stock symbol and period of interest, load data from yahoo finance and return a panda dataframe """

    # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max

    # example input: symbol = ["SPY", "APPL"] period = "5y"
    # will download data for SPY and Apple for the past 5 year from today

    try: 
        DF = yf.download(symbol_list, period = period)
        return (DF)
    except:
        print ("Failure parsing Yahoo Finance Data")
    
def select_adjclose_column (DF):
    """given a yahoo finance dataframe, select the adjusted close column"""

    return (DF["Adj Close"])


def fill_missing_values (DF):
    """ given a yahoo finance dataframe
    in case there are missing values, foward fill first followed by back fill """
    DF = DF.fillna(method = "ffill")
    DF = DF.fillna(method = "bfill")
    return (DF)

def compute_monthly_return(DF):
    """ given a yahoo finance dataframe, calculate monthly return """
    return (DF.resample('M').ffill().pct_change()[1:])

def compute_mean_return (DF, show = False):
    """ given a dataframe, calculate mean return for each column """
    if (show == True):
        DF_temp = pd.DataFrame(DF.mean(), columns = ["Mean Return"])

        print ("The risk of the selected stocks are the following: ")
        display (DF_temp)

    return (DF.mean())


def compute_covariance(DF):
    """ given a dataframe, calcualte covariance"""
    return (DF.cov())


def compute_variance(DF, show = False):
    """ given a dataframe, calcualte variance"""

    if (show == True):
        DF_temp = pd.DataFrame(DF.var(), columns = ["Variance"])
        display (DF_temp)
    return (DF.var())

def compute_std(DF, show = False):
    """ given a dataframe of stock return, calcualte standard deviation (or risk)"""

    if (show == True):
        DF_temp = pd.DataFrame(DF.std(), columns = ["std (risk"])
        display (DF_temp)
    return (DF.std())

def compute_sharpe_ratio(DF, period = "M", risk_free_rate = 0):
    
    """calcuate sharpe ratio for individual stocks given a dataframe (containing return data)

    Parameters: 
    DF: A dataframe containing monthly return

    period has three options 
    "M" stands for monthly
    "W" stands for weekly
    "D" stands for daily
    
    the risk_free_rate is assumed to be annual rate, defaulted to be zero

    Returns:
    A dataframe containing sharpe ratio for each stock

    """
    # calculate the coefficient and make the rate to the corresponding period

    if (period == "M"):
        coef = np.array(12**0.5)
        risk_free_rate = np.array(risk_free_rate/12.0)
    elif (period == "W"):
        coef = np.array(52**0.5)
        risk_free_rate = np.array(risk_free_rate/52.0)
    elif (period == "D"):
        coef  = np.array(252**0.5)
        risk_free_rate = np.array(risk_free_rate/252.0)
    else:
        print ("period not specfied or not in one of the available values, assumed the period to be monthly")
        coef = np.array(12**0.5)

    temp_DF = coef * (DF.mean() - risk_free_rate)/DF.std()

    return (temp_DF)


def compute_sharpe_ratio_portfolio(DF, weight, period = "M", risk_free_rate = 0):
    
    """calcuate sharpe ratio for the entire portfolio given a dataframe containing return data

    Parameters: 
    DF: A dataframe containing monthly return
    weight:  a list of float indicating the weight of the stocks in the portfolio

    period has three options 
    "M" stands for monthly
    "W" stands for weekly
    "D" stands for daily

    the risk_free_rate is assumed to be annual rate, defaulted to be zero

    Returns:
    A float indicating the sharpe ratio of the portfolio
    """
    # calculate the coefficient and make the rate to the corresponding period

    if (period == "M"):
        coef = np.array(12**0.5)
        risk_free_rate = np.array(risk_free_rate/12.0)
    elif (period == "W"):
        coef = np.array(52**0.5)
        risk_free_rate = np.array(risk_free_rate/52.0)
    elif (period == "D"):
        coef  = np.array(252**0.5)
        risk_free_rate = np.array(risk_free_rate/252.0)
    else:
        print ("period not specfied or not in one of the available values, assumed the period to be monthly")
        coef = np.array(12**0.5)

    weight = np.array(weight)

    # calcuate return by date (mean columnwise)
    weighted_return = DF.multiply(weight).mean(axis = 1)

    mean_return = weighted_return.mean()
    std = weighted_return.std()

    sharpe_ratio = coef * (mean_return - risk_free_rate)/std

    return (sharpe_ratio)








#%% [markdown]

### 2. Optimization

#### 2.1 Select symbols to analyze

# For this example, I gather the past 5 years of data for the Dow Jones 30 Index and calculated monthly return using adjusted close. 


#%% 


# select Dow Jones 30 Index's holdings
symbol_list = ["MMM", "AXP", "AAPL", "BA", "CAT", "CVX", "CSCO", "KO", "DOW", "XOM", "GS", "HD", "IBM", "INTC", "JNJ", "JPM", "MCD","MRK", "MSFT", "NKE", "PFE", "PG", "TRV", "UNH", "UTX", "VZ", "V", "WMT", "WBA", "DIS"]

# Load Yahoo Data
DF =  load_symbol(symbol_list, period = "5y")

# select adjusted close and fill missing values (especially for the DOW Company)
DF = fill_missing_values(select_adjclose_column(DF))

# calculate monthly return and assign it to DF1
DF1 = compute_monthly_return(DF)
DF1.head(10)






#%% [markdown]

#### 2.2 Set and solve optimization problem using the strategies of minimizing risk given a required return

#%% 
# set up for optimization problems
# number of stocks
n = len(DF1.columns)

# set up the composition of stocks in the portfolio
x = cp.Variable(n)

# convert return dataframe to matrix form then transpose
mean_return = compute_mean_return(DF1).values

print ("For the selected period, the average monthly return for all stock is {:.4f}%".format(100.0 * mean_return.mean()))

print ("For the selected period, the maximum monthly return for all stock is {:.4f}%".format(100.0 * mean_return.max()))

# specify required return
req_return = 0.015

# Calculate expected return
expected_return = mean_return.T*x

# compute risk
risk = cp.quad_form(x, compute_covariance(DF1))

# Set up objective and contraints
# 1. objective is minimize risk
objective = cp.Minimize(risk)

# 2. constains include sum of x must be 1, x must be >= 0
# expected return should be greater than required return
# each individual stock could not be higher than a certain percentage (diversification)

constraints = [cp.sum(x) == 1, expected_return >= req_return, x >=0, x <= 0.3]

prob = cp.Problem(objective, constraints)

# solve problem and write solution
try:
    prob.solve()

    # after the .solve() method 
    # the value of x will change since it is a cp.Variable object

    print ("----------------------")
    print ("Optimal portfolio")
    print ("----------------------")

    portfolio_DF = pd.DataFrame({"Ticker":symbol_list, "Percentage": np.round(x.value,4)*np.array(100.0)})

    display(portfolio_DF)


    print ("----------------------")

    print ('Exp return = {:.4f}%'.format(expected_return .value*100))
    print ('risk    = {:.4f}'.format((risk.value)**0.5))

    print ("----------------------")
except:
    print ('Error')



#%% [markdown]

#### 2.3 Wrap the optimization routine in function and obtain efficient frontier

def compute_frontier(DF, max_indi_allocation = 0.3, num_points = 50):

    """Compute the weights, return, and risk for plot the efficent frontier 
    
    Paramters:
    DF: A dataframe of stocks with returns
    min_ticker_count
    max_indi_allocation: maximum portfolio allocation for each stock
    num_points: An integer indicating the number of points for simulation


    Returns:
    A tuple of numpy arrays
    (weights, mean_return, standard_deviation, sharpe ratio)

    """

    n = len(DF.columns)
    
    x = cp.Variable(n)

    mean_return = compute_mean_return(DF).values

    max_return = mean_return.max() #obtain maximum return for the stocks

    return_vector = np.linspace(0,max_return, num_points)


    # initialize numpy array for storing results
    weight_vector = np.zeros((1, n))
    risk_vector = np.zeros((0))
    expected_return_vector = np.zeros((0))
    sharpe_vector = np.zeros((0))

    for (index, req_return) in enumerate(return_vector):

        print (index,req_return)



        expected_return = mean_return.T*x
        risk = cp.quad_form(x, compute_covariance(DF))

        objective = cp.Minimize(risk)

        constraints = [cp.sum(x) == 1, expected_return >= req_return, x >= 0, x <= max_indi_allocation]

        prob = cp.Problem(objective, constraints)

        try:
            prob.solve()

           
            print ("Optimal portfolio")
            print ("----------------------")

            print ('Exp return = {:.4f}%'.format(expected_return .value*100))
            print ('risk    = {:.4f}'.format((risk.value)**0.5))

            # append to vector

            print (x.value.shape)

            weight_vector = np.append(weight_vector, x.value.reshape(1,n), axis = 0)

            risk_vector = np.append(risk_vector, (risk.value)**0.5)

            expected_return_vector = np.append(expected_return_vector, expected_return.value)

            sharpe_vector = np.append(sharpe_vector, compute_sharpe_ratio_portfolio(DF, x.value))
        except:
            # if there is no solution, do nothing
            pass
            

    print ("finished looping")

    return (weight_vector.round(4), expected_return_vector.round(4), risk_vector.round(4), sharpe_vector.round(4))


# run the above function
(weight,ret, std,sharpe) = compute_frontier(DF1)

#%% [markdown]

#### 2.4 Plot Efficient Frontier

# The Efficient Frontier show the minimum risk for the given level of return. The ratio of return/standard deviation is also called the sharpe ratio (risk adjusted return)

# In the plot below, the blue line indicating the efficiency frontier, and the red diamond indicates the monthly return and standard deviation for each stock in the selection

#%% 
#import library
from bokeh.plotting import figure, output_file, show
from bokeh.io import output_notebook
from bokeh.models import LinearAxis, Range1d

# display plot inline in notebook
output_notebook()

p = figure(x_axis_label = "Standard Deviation", y_axis_label = "monthly return", plot_width=600, plot_height=400, title="Efficient Fronter")

# add a line renderer
p.line(std, ret, line_width=2, legend = "Optimized Portfolio")

# add individual simulation point
p.circle(std,ret,size = 4)

# add individual point for each stock
p.diamond(compute_std(DF1).values, compute_mean_return(DF1).values, color = "red", size = 4, legend = "Individual Stocks")

p.y_range = Range1d(0,np.nanmax(ret) + 0.005)


# add the sharpe ratio for the portfolio as the second y axis
p.extra_y_ranges = {"sharpe":Range1d(start = 0, end = 2.5)}
p.add_layout(LinearAxis(y_range_name = "sharpe", axis_label='Sharpe Ratio'), "right")
p.triangle(std,sharpe, size = 4, color = "orange", y_range_name = "sharpe", legend = "Sharpe Ratio")
p.legend.location = "bottom_left"
show(p)

#%% [markdown]
### 2.5 Best Portfolio so far

# Based on the plot above, I would select the portfolio with the highest sharpe ratio, which has approximately 1.8% of monthly return with a standard deviation of 0.032.

# The dataframe belows shows the optimized portfolio after considering Sharpe Ratio. 

#%%
portfolio_DF = pd.DataFrame({"Ticker":symbol_list, "Percentage": 100.0*weight[np.argmax(sharpe)]})

display(portfolio_DF[portfolio_DF["Percentage"] > 0.0001])


#%%
