import numpy as np
import pandas as pd
# Function for outlier capping with IQR
def cap_outliers_iqr(X):
    X = pd.DataFrame(X) # Convert the input to a pandas DataFrame if it's not already
    X.columns = ['AFDP', 'TIT', 'CDP', 'CO']  # Set the column names for the DataFrame
    for col in X.columns:
        Q1 = X[col].quantile(0.25)
        Q3 = X[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        X[col] = np.where(X[col] < lower_bound, lower_bound, np.where(X[col] > upper_bound, upper_bound, X[col]))
    return X.to_numpy() # Convert the DataFrame back to a NumPy array before returning

# Function to apply square transformation to specific columns
def square_transform(X):
    X_df = pd.DataFrame(X, columns=['AFDP', 'TIT', 'CDP', 'CO']) # New DataFrame with column names
    X_df['TIT'] = np.square(X_df['TIT']) # Transformation on new DataFrame
    return X_df.to_numpy() # Convert back to numpy array

# Function to apply log1p transformation to specific columns
def log1p_transform(X):
    X_df = pd.DataFrame(X, columns=['AFDP', 'TIT', 'CDP', 'CO']) # New DataFrame with column names
    X_df['CO'] = np.log1p(X_df['CO']) # Transformation on new DataFrame
    return X_df.to_numpy() # Convert back to numpy array