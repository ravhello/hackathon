import pandas as pd
from sklearn.preprocessing import MinMaxScaler

class Recommender:
    def __init__(self, df):
        self.df = df

    def get_recommendations(self, user_age, user):
        pass

def get_personalized_recommendations(df, user_age, user, model):
    return model.get_recommendations(user_age, user)


# def get_generic_recommendations(transactions, n_recommendations=12):
#     """
#     Identify the top N most sold products with normalized popularity scores.
    
#     Parameters:
#         transactions (DataFrame): The transactions data containing all required information
#         n_recommendations (int): Number of products to recommend (default=12)
    
#     Returns:
#         DataFrame: Top N most sold products with all their product information and popularity scores
#     """
#     if transactions.empty:
#         return transactions
        
#     # Ensure the 'TransactionDate' column is in datetime format
#     transactions['TransactionDate'] = pd.to_datetime(transactions['TransactionDate'])
    
#     # Group by ProductID and aggregate all necessary fields
#     product_metrics = transactions.groupby('ProductID').agg({
#         'Quantity_sold': 'sum',
#         'Price': 'mean',  # This will become avg_price
#         'Universe': 'first',
#         'Category': 'first',
#         'FamilyLevel1': 'first',
#         'FamilyLevel2': 'first'
#     }).reset_index()
    
#     # Rename Price column to avg_price
#     product_metrics = product_metrics.rename(columns={'Price': 'avg_price'})
    
#     # Add popularity score using MinMaxScaler
#     scaler = MinMaxScaler()
#     product_metrics['popularity_score'] = scaler.fit_transform(
#         product_metrics[['Quantity_sold']]
#     )
    
#     # Randomize the popularity scores (if you want to maintain this feature)
#     product_metrics['popularity_score'] = product_metrics['popularity_score'].sample(frac=1).reset_index(drop=True)
    
#     # Get top N products by popularity score
#     top_products = product_metrics.nlargest(n_recommendations, 'popularity_score')
    
#     return top_products


def get_generic_recommendations(transactions, n_recommendations=18):

    """
    Identify the top 5 most sold products during a given date range.
    
    Parameters:
        transactions (DataFrame): The transactions data containing 'SaleTransactionDate', 'ProductID', and 'Quantity'.
        start_date (str): Start date of the peak period (format: 'YYYY-MM-DD').
        end_date (str): End date of the peak period (format: 'YYYY-MM-DD').
    
    Returns:
        DataFrame: Top 5 most sold products with their total quantity sold.
    """
    # Ensure the 'SaleTransactionDate' column is in datetime format
    transactions['TransactionDate'] = pd.to_datetime(transactions['TransactionDate'])
    
    # Filter transactions within the specified date range
    peak_period_transactions = transactions[
        (transactions['TransactionDate'] >= transactions['TransactionDate'].min()) & 
        (transactions['TransactionDate'] <= transactions['TransactionDate'].max())
    ]
    
    # Group by 'ProductID' and sum the quantities
    product_sales = peak_period_transactions.groupby('ProductID')['Quantity_sold'].sum()
    
    # Sort by quantity in descending order and get the top 5 products
    top_products = product_sales.sort_values(ascending=False).head(n_recommendations)
    
    return top_products.reset_index()





def get_generic_recommendations(df, n_recommendations=18, country="FRA"):
    if df.empty:
        return df
        
    # Filter transactions for the specified country
    country_transactions = df[df['StoreCountry'] == country]
    
    product_metrics = country_transactions.groupby('ProductID').agg(
    {
        'Quantity_sold': 'sum',
        'avg_price': 'first',
        'Universe': 'first',
        'Category': 'first',
        'FamilyLevel1': 'first',
        'FamilyLevel2': 'first'
    }).reset_index()
    
    scaler = MinMaxScaler()
    product_metrics['popularity_score'] = scaler.fit_transform(
        product_metrics[['Quantity_sold']]
    )

    # # randomized the popularity_scores
    # product_metrics['popularity_score'] = product_metrics['popularity_score'].sample(frac=1).reset_index(drop=True)
    
    return product_metrics.nlargest(n_recommendations, 'popularity_score')


# import pandas as pd
# from sklearn.preprocessing import MinMaxScaler

# def get_generic_recommendations(df, n_recommendations=12, start_date=None, end_date=None):
#     """
#     Identify the top N most sold products during a given date range.

#     Parameters:
#         df (DataFrame): The transactions data containing 'SaleTransactionDate', 'ProductID', 'Quantity_sold', 'avg_price', 'Universe', 'Category', 'FamilyLevel1', and 'FamilyLevel2'.
#         n_recommendations (int): Number of top products to return.
#         start_date (str, optional): Start date of the peak period (format: 'YYYY-MM-DD').
#         end_date (str, optional): End date of the peak period (format: 'YYYY-MM-DD').

#     Returns:
#         DataFrame: Top N most sold products with their popularity score.
#     """
#     if df.empty:
#         return df

#     # Ensure the 'SaleTransactionDate' column is in datetime format
#     df['SaleTransactionDate'] = pd.to_datetime(df['SaleTransactionDate'])

#     # Filter transactions within the specified date range
#     if start_date and end_date:
#         peak_period_transactions = df[
#             (df['SaleTransactionDate'] >= start_date) &
#             (df['SaleTransactionDate'] <= end_date)
#         ]
#     else:
#         peak_period_transactions = df

#     # Group by 'ProductID' and aggregate necessary metrics
#     product_metrics = peak_period_transactions.groupby('ProductID').agg({
#         'Quantity_sold': 'sum',
#         'avg_price': 'first',
#         'Universe': 'first',
#         'Category': 'first',
#         'FamilyLevel1': 'first',
#         'FamilyLevel2': 'first'
#     }).reset_index()

#     scaler = MinMaxScaler()
#     product_metrics['popularity_score'] = scaler.fit_transform(
#         product_metrics[['Quantity_sold']]
#     )

#     # Get the top N products based on the popularity score
#     return product_metrics.nlargest(n_recommendations, 'popularity_score')



def get_personalized_recommendations(df, user_data, n_recommendations=18):
    if df.empty:
        return df
        
    # Add your personalization logic here
    # For now, return generic recommendations
    return get_generic_recommendations(df, n_recommendations)