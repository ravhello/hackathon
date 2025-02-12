def top_sold_products(n, transactions, start_date, end_date):
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
        (transactions['TransactionDate'] >= start_date) & 
        (transactions['TransactionDate'] <= end_date)
    ]
    
    # Group by 'ProductID' and sum the quantities
    product_sales = peak_period_transactions.groupby('ProductID')['Quantity_sold'].sum()
    
    # Sort by quantity in descending order and get the top 5 products
    top_products = product_sales.sort_values(ascending=False).head(n)
    
    return top_products.reset_index()


'''
Example usage
'''

# Example usage
# # Define the date range for the peak period
# start_date = '2024-10-01'
# end_date = '2025-01-31'

# # Assuming 'transactions' is your DataFrame
# top_products_during_peak = top_sold_products(3, df, start_date, end_date)
# top_products_during_peak['ProductID'] = top_products_during_peak['ProductID'].apply(lambda x: fetch_product(x, df))
# top_products_during_peak
