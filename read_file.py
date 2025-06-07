import pandas as pd

def read_file(file_path):
    """
    Reads a CSV file and returns a DataFrame.
    
    Parameters:
    file_path (str): The path to the CSV file.
    
    Returns:
    pd.DataFrame: The DataFrame containing the data from the CSV file.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=None)

        # get the 5th row with the column names
        columns = df['Listado'].iloc[5]

        # reset the index and set the column names 
        df['Listado'].columns = columns
        df['Listado'] = df['Listado'].iloc[6:]

        # remove rows with all NaN values
        df['Listado'] = df['Listado'].dropna(how='all')

        # reset the index
        df['Listado'].reset_index(drop=True, inplace=True)

        return df
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None
    
if __name__ == "__main__":
    movimientos_file = 'movimientos/movimientos.xls'
    df = read_file(movimientos_file)
    if df is not None:
        print(df['Listado'].head())
    else:
        print("Failed to read the file.")