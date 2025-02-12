def plot_product_curve(product_ID, df):
    df['SaleTransactionDate'] = df['SaleTransactionDate'].astype(str).str[:10]
    df['SaleTransactionDate'] = pd.to_datetime(df['SaleTransactionDate'])

    prods = df[df['ProductID']==product_ID]
    prods = prods.sort_values(by='SaleTransactionDate')

    plt.figure(figsize=(10, 5))
    plt.plot(prods['SaleTransactionDate'], prods['SalesNetAmountEuro'], linestyle='-')

    # Labels and title
    # plt.xlabel('Date')
    plt.ylabel('Sales')
    plt.title(f'Sales Trend for Product ID {product_ID}')
    plt.xticks(rotation=45)
    plt.grid()

    # Show plot
    plt.show()

# Example usage
# plot_product_curve(3532473209579560668)