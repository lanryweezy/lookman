import pandas as pd

def analyze_excel(file_path):
    df = pd.read_excel(file_path, header=2) # Data starts from row 3 (index 2)
    df.columns = df.iloc[0] # Set the first row as header
    df = df[1:].reset_index(drop=True) # Remove the first row and reset index

    # Drop columns that are entirely NaN or not relevant after initial inspection
    df = df.dropna(axis=1, how='all')
    
    # Clean up column names by stripping whitespace
    df.columns = df.columns.str.strip()

    print(df.head())
    print(df.columns)
    print(df.info())

if __name__ == '__main__':
    analyze_excel('/home/ubuntu/upload/ADELABLOANREPAYMENTSCHEDULE.xlsx')

