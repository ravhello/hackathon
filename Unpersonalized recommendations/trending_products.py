import pandas as pd

def get_trending_products(data, specific_date='2025-02-15', time_window=1, quantity_based=False, k=5, country='', storeID = ''):
    """
    Returns a list of dictionaries containing the top k trending products based on the number of units sold
    or total sales amount within the time window ending at specific_date.

    Parameters:
      data (pd.DataFrame): DataFrame containing transaction data.
      specific_date (str or pd.Timestamp): The end date for the time window (e.g., '2023-01-02').
      time_window (int): The number of days to look back from specific_date.
      quantity_based (bool): If True, the top k products are based on the quantity sold, else based on total sales amount.
      k (int): Number of top products to return.
      country (str): If specified, filters transactions by StoreCountry. If empty (''), no country filtering is applied.
      storeID (str): If specified, filters transactions by StoreID. If empty (''), no storeID filtering is applied.

    Returns:
      list: A list of dictionaries containing product details.
    """
    # Ensure that TransactionDate is a datetime column
    data['TransactionDate'] = pd.to_datetime(data['TransactionDate'])
    
    # Convert the specific_date input to a timezone-aware datetime with UTC
    end_date = pd.to_datetime(specific_date, utc=True)
    
    # Define the start date of the time window
    start_date = end_date - pd.Timedelta(days=time_window)
    
    # Filter transactions by date range
    mask = (data['TransactionDate'] >= start_date) & (data['TransactionDate'] <= end_date)
    window_data = data.loc[mask]
    
    # Apply country filter if a country is specified
    if country:
        window_data = window_data[window_data['StoreCountry'] == country]

    if storeID:
        window_data = window_data[window_data['StoreID'] == storeID]
    
    # Determine the metric to use for ranking products
    metric = 'Quantity_sold' if quantity_based else 'SalesNetAmountEuro'
    
    # Aggregate total quantity sold or total sales amount for each product
    product_sales = window_data.groupby('ProductID')[[metric]].sum().reset_index()
    
    # Merge with product metadata (Category, FamilyLevel1, Brand)
    product_details = window_data[['ProductID', 'Category', 'FamilyLevel1', 'Brand']].drop_duplicates()
    merged_data = pd.merge(product_sales, product_details, on='ProductID', how='left')
    
    # Sort products by the chosen metric in descending order and select the top k
    top_products = merged_data.sort_values(by=metric, ascending=False).head(k)
    
    # Convert to a list of dictionaries
    trending_products = top_products.to_dict(orient='records')
    
    return trending_products
