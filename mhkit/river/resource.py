import pandas as pd
import numpy as np
from scipy.stats import linregress as _linregress
from scipy.stats import rv_histogram as _rv_histogram


def Froude_number(v, h, g=9.80665):
    """
    Calculate the Froude Number of the river, channel or duct flow,
    to check subcritical flow assumption (if Fr <1).
    
    Parameters
    ------------
    v : int/float 
        Average velocity [m/s].
    h : int/float
        Mean hydraulic depth float [m].
    g : int/float
        Gravitational acceleration [m/s2].

    Returns
    ---------
    Fr : float
        Froude Number of the river [unitless].

    """
    if not isinstance(v, (int,float)):
        raise TypeError(f'v must be of type int or float. Got: {type(v)}')
    if not isinstance(h, (int,float)):
        raise TypeError(f'h must be of type int or float. Got: {type(h)}')
    if not isinstance(g, (int,float)):
        raise TypeError(f'g must be of type int or float. Got: {type(g)}')
    
    Fr = v / np.sqrt( g * h )
    
    return Fr 


def exceedance_probability(D):
    """
    Calculates the exceedance probability
    
    Parameters
    ----------
    D : pandas Series
        Data indexed by time [datetime or s].  
        
    Returns   
    -------
    F : pandas DataFrame    
        Exceedance probability [unitless] indexed by time [datetime or s]
    """
    # dataframe allowed for matlab
    if not isinstance(D, (pd.DataFrame, pd.Series)):
        raise TypeError(f'D must be of type pd.Series or pd.DataFrame. Got: {type(D)}')
    
    if isinstance(D, pd.DataFrame) and len(D.columns) == 1: # for matlab
        D = D.squeeze().copy()

    # Calculate exceedence probability (F)
    rank = D.rank(method='max', ascending=False)
    F = 100* (rank / (len(D)+1) )
    
    F = F.to_frame('F') # for matlab
    
    return F


def polynomial_fit(x, y, n):
    """
    Returns a polynomial fit for y given x of order n
    with an R-squared score of the fit

    Parameters
    -----------
    x : numpy array
        x data for polynomial fit.
    y : numpy array
        y data for polynomial fit.
    n : int
        order of the polynomial fit.

    Returns
    ----------
    polynomial_coefficients : numpy polynomial
        List of polynomial coefficients
    R2 : float
        Polynomical fit coeffcient of determination
    
    """
    try:
        x = np.array(x)
    except:
        pass
    try:
        y = np.array(y)
    except:
        pass
    if not isinstance(x, np.ndarray):
        raise TypeError(f'x must be of type np.ndarray. Got: {type(x)}')
    if not isinstance(y, np.ndarray):
        raise TypeError(f'y must be of type np.ndarray. Got: {type(y)}')
    if not isinstance(n, int):
        raise TypeError(f'n must be of type int. Got: {type(n)}')
    
    # Get coeffcients of polynomial of order n 
    polynomial_coefficients = np.poly1d(np.polyfit(x, y, n))
    
    # Calculate the coeffcient of determination
    slope, intercept, r_value, p_value, std_err = _linregress(y, polynomial_coefficients(x))
    R2 = r_value**2
    
    return polynomial_coefficients, R2
    

def discharge_to_velocity(D, polynomial_coefficients):
    """
    Calculates velocity given discharge data and the relationship between 
    discharge and velocity at an individual turbine
    
    Parameters
    ------------
    D : pandas Series
        Discharge data [m3/s] indexed by time [datetime or s]
    polynomial_coefficients : numpy polynomial
        List of polynomial coefficients that discribe the relationship between 
        discharge and velocity at an individual turbine
    
    Returns   
    ------------
    V: pandas DataFrame   
        Velocity [m/s] indexed by time [datetime or s]
    """
    # dataframe allowed for matlab
    if not isinstance(D, (pd.DataFrame, pd.Series)):
        raise TypeError(f'D must be of type pd.Series. Got: {type(D)}')
    if not isinstance(polynomial_coefficients, np.poly1d):
        raise TypeError(f'polynomial_coefficients must be of type np.poly1d. Got: {type(polynomial_coefficients)}')
    
    if isinstance(D, pd.DataFrame) and len(D.columns) == 1: # for matlab
        D = D.squeeze().copy()
        
    # Calculate velocity using polynomial
    vals = polynomial_coefficients(D)
    V = pd.Series(vals, index=D.index)
    
    V = V.to_frame('V') # for matlab
    
    return V

    
def velocity_to_power(V, polynomial_coefficients, cut_in, cut_out):
    """
    Calculates power given velocity data and the relationship 
    between velocity and power from an individual turbine
    
    Parameters
    ----------
    V : pandas Series
        Velocity [m/s] indexed by time [datetime or s]
    polynomial_coefficients : numpy polynomial
        List of polynomial coefficients that discribe the relationship between 
        velocity and power at an individual turbine
    cut_in: int/float
        Velocity values below cut_in are not used to compute P
    cut_out: int/float
        Velocity values above cut_out are not used to compute P
    
    Returns   
    -------
    P : pandas DataFrame
        Power [W] indexed by time [datetime or s]
    """
    # dataframe allowed for matlab
    if not isinstance(V, (pd.DataFrame, pd.Series)):
        raise TypeError(f'V must be of type pd.Series or pd.DataFrame. Got: {type(V)}')
    if not isinstance(polynomial_coefficients, np.poly1d):
        raise TypeError(f'polynomial_coefficients must be of type np.poly1d. Got: {type(polynomial_coefficients)}')
    if not isinstance(cut_in, (int,float)):
        raise TypeError(f'cut_in must be of type int or float. Got: {type(cut_in)}')
    if not isinstance(cut_out, (int,float)):
        raise TypeError(f'cut_out must be of type int or float. Got: {type(cut_out)}')
    
    if isinstance(V, pd.DataFrame) and len(V.columns) == 1:
        V = V.squeeze().copy()
        
    # Calculate power using tranfer function and FDC
    vals = polynomial_coefficients(V)
    
    # Power for velocity values outside lower and upper bounds Turbine produces 0 power
    vals[V < cut_in] = 0.
    vals[V > cut_out] = 0.

    P = pd.Series(vals, index=V.index)
    
    P = P.to_frame('P') # for matlab
    
    return P


def energy_produced(P, seconds):
    """
    Returns the energy produced for a given time period provided
    exceedence probability and power.
    
    Parameters
    ----------
    P : pandas Series
        Power [W] indexed by time [datetime or s]
    seconds: int or float
        Seconds in the time period of interest
            
    Returns
    -------
    E : float
        Energy [J] produced in the given time frame
    """
    # dataframe allowed for matlab
    if not isinstance(P, (pd.DataFrame, pd.Series)):
        raise TypeError(f'P must be of type pd.Series or pd.DataFrame. Got: {type(P)}')
    if not isinstance(seconds, (int, float)):
        raise TypeError(f'seconds must be of type int or float. Got: {type(seconds)}')

    if isinstance(P, pd.DataFrame) and len(P.columns) == 1: # for matlab
        P = P.squeeze().copy()
        
    # Calculate Histogram of power
    H, edges = np.histogram(P, 100 )
    # Create a distribution
    hist_dist = _rv_histogram([H,edges])
    # Sample range for pdf
    x = np.linspace(edges.min(),edges.max(),1000) 
    # Calculate the expected value of Power
    expected_val_of_power = np.trapz(x*hist_dist.pdf(x),x=x)
    # Note: Built-in Expected Value method often throws warning
    #EV = hist_dist.expect(lb=edges.min(), ub=edges.max())
    # Energy
    E = seconds * expected_val_of_power 
    
    return E

