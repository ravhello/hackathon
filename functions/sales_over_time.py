def sales_over_time(df):

    # Aggregate sales over time
    df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
    transactions_time_series = df.groupby(['TransactionDate'])['Quantity_sold'].sum()

    # Plot trends
    transactions_time_series.rolling(window=30).mean().plot(figsize=(12,6))
    plt.title('Monthly Sales Trend')
    plt.show()

'''
example usage

sales_over_time(df)

'''