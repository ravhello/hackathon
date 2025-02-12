def get_top_products_by_store(transactions, StoreCountry):
    # Filter transactions by the given StoreCountry
    store_transactions = transactions[transactions['StoreCountry'] == StoreCountry]

    # Group by ProductID and sum quantities
    df_store = store_transactions.groupby(['ProductID'])['Quantity_sold'].sum().reset_index()

    # Get the top 5 products by quantity
    top_products_per_store = df_store.nlargest(5, 'Quantity_sold')

    # Fetch product information for the top products
    # top_products_per_store['ProductID'] = top_products_per_store['ProductID'].apply(lambda x: fetch_product(x))

    return top_products_per_store

# ClientCountry = 'USA'
# top_products = get_top_products_by_store(df, ClientCountry)
# print(top_products)