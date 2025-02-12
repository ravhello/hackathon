from sklearn.preprocessing import MinMaxScaler

class Recommender:
    def __init__(self, df):
        self.df = df

    def get_recommendations(self, user_age, user):
        pass

def get_personalized_recommendations(df, user_age, user, model):
    return model.get_recommendations(user_age, user)


def get_generic_recommendations(df, n_recommendations=12):
    if df.empty:
        return df
        
    product_metrics = df.groupby('ProductID').agg({
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

    # randomized the popularity_scores
    product_metrics['popularity_score'] = product_metrics['popularity_score'].sample(frac=1).reset_index(drop=True)
    
    return product_metrics.nlargest(n_recommendations, 'popularity_score')

def get_personalized_recommendations(df, user_data, n_recommendations=12):
    if df.empty:
        return df
        
    # Add your personalization logic here
    # For now, return generic recommendations
    return get_generic_recommendations(df, n_recommendations)