"""
recommendation_system.py

This script implements an online recommendation system using River.
It includes:
  - A training function that loads data, builds the feature pipeline, trains the model with negative sampling, and saves the model.
  - A function to load a pre-existing model.
  - A function to evaluate the model on a specific row of the test set.
  - A function to create recommendations for a customer given their customer ID.

Usage:
  To train the model:
      python recommendation_system.py --train
  To evaluate a specific test row (by row index):
      python recommendation_system.py --evaluate --row_index 0
  To get recommendations for a given customer ID:
      python recommendation_system.py --recommend CUSTOMER_ID
"""

import os
import argparse
import random
import pickle
from collections import defaultdict

import numpy as np
import pandas as pd

# River modules
from river import compose, base, preprocessing, feature_extraction, ensemble, tree, metrics
from river import forest
from river.compose import Pipeline

# =============================================================================
# Global Definitions & Default Values
# =============================================================================

# Default values for any missing features.
default_values = {
    'StoreCountry': 'USA',
    'Category': 'Unknown',
    'FamilyLevel1': 'Unknown',
    'FamilyLevel2': 'Unknown',
    'Universe': 'Unknown',
    'ClientSegment': 'Unknown',
    'ClientGender': 'Unknown',
    'ClientCountry': 'USA',
    'ClientOptINEmail': False,
    'ClientOptINPhone': False,
    'Weekday': 'Unknown',
    'Brand': 'Unknown',
    'DayOfWeek': 'Unknown',
    'Month': 'January',
    'Season': 'Unknown',
    # Numerical defaults
    'Age': 0,
    'Quantity_sold': 0,
    'SalesNetAmountEuro': 0,
    'product_avg_price_order': 0,
    'avg_price': 0,
    'DaysSinceLastTransaction': 0,
    'CumulativeSpent': 0,
    'CumulativeQuantity': 0,
    'PercentageMaleProductsSoFar': 0,
    'UniqueProductsSoFar': 0,
    'AverageAmountPerTransactionSoFar': 0,
    'AverageFrequencySoFar': 0,
    'AveragePrice': 0,
    'Frequency_30': 0,
    'Monetary_30': 0,
    'Recency_30': 0,
    'Frequency_60': 0,
    'Monetary_60': 0,
    'Recency_60': 0,
    'Frequency_90': 0,
    'Monetary_90': 0,
    'Recency_90': 0
}

# Feature groups for the pipeline.
CATEGORICAL_FEATURES = [
    'StoreCountry', 'Category', 'FamilyLevel1', 'FamilyLevel2', 'Universe',
    'ClientSegment', 'ClientGender', 'ClientCountry', 'ClientOptINEmail', 'ClientOptINPhone',
    'Weekday', 'Brand', 'DayOfWeek', 'Month', 'Season'
]

NUMERICAL_FEATURES = [
    'Age', 'Quantity_sold', 'SalesNetAmountEuro', 'product_avg_price_order', 'avg_price',
    'DaysSinceLastTransaction', 'CumulativeSpent', 'CumulativeQuantity', 'PercentageMaleProductsSoFar',
    'UniqueProductsSoFar', 'AverageAmountPerTransactionSoFar', 'AverageFrequencySoFar', 'AveragePrice',
    'Frequency_30', 'Monetary_30', 'Recency_30', 'Frequency_60', 'Monetary_60', 'Recency_60',
    'Frequency_90', 'Monetary_90', 'Recency_90'
]

# Build individual pipelines.
cat_pipeline = compose.Select(*CATEGORICAL_FEATURES) | preprocessing.OneHotEncoder()
num_pipeline = compose.Select(*NUMERICAL_FEATURES) | preprocessing.StandardScaler()
feature_pipeline = compose.TransformerUnion(cat_pipeline, num_pipeline)

# =============================================================================
# Custom Transformer for Missing Indicators
# =============================================================================
class MissingIndicator(base.Transformer):
    """Adds missing indicators for selected keys."""
    def __init__(self, keys):
        self.keys = keys
    def transform_one(self, x):
        for key in self.keys:
            if x.get(key) is None or (isinstance(x.get(key), float) and np.isnan(x.get(key))):
                x[f'{key}_missing'] = 1
            else:
                x[f'{key}_missing'] = 0
        return x
    def learn_one(self, x):
        return self.transform_one(x)

missing_indicator = MissingIndicator(keys=['Age', 'ClientGender'])
missing_indicator_transformer = compose.FuncTransformer(missing_indicator.transform_one)

# Build model pipelines.
pipeline_arf = Pipeline(
    missing_indicator_transformer,
    feature_pipeline,
    forest.ARFClassifier()
)

pipeline_hat = Pipeline(
    missing_indicator_transformer,
    feature_pipeline,
    tree.HoeffdingAdaptiveTreeClassifier()
)
# =============================================================================
# Data & Product Catalog
# =============================================================================

# Assumed location of the data file in the repo.
DATA_PATH = os.path.join(os.path.dirname(__file__), 'final_df.parquet')

# Product-related columns.
product_cols = ['ProductID', 'StoreCountry', 'Category', 'FamilyLevel1', 'FamilyLevel2', 'Universe']

def load_data(data_path=DATA_PATH):
    data = pd.read_parquet(data_path)
    # Drop rolling percentage columns if present.
    cols_to_drop = [
        'Rolling90Pct_Football', 'Rolling90Pct_Handball', 'Rolling90Pct_Badminton',
        'Rolling90Pct_Baseball', 'Rolling90Pct_Tennis', 'Rolling90Pct_Hockey',
        'Rolling90Pct_Cricket', 'Rolling90Pct_Beach', 'Rolling90Pct_Basketball',
        'Rolling90Pct_Rugby', 'Rolling90Pct_Golf', 'Rolling90Pct_Softball',
        'Rolling90Pct_Cycling', 'Rolling90Pct_Volleyball', 'Rolling90Pct_Running',
        'Rolling90Pct_Skiing'
    ]
    data.drop(columns=cols_to_drop, inplace=True, errors='ignore')
    return data

def build_product_catalog(data):
    all_products = data[product_cols].drop_duplicates().to_dict('records')
    products_by_country = defaultdict(list)
    for prod in all_products:
        country = prod.get('StoreCountry')
        if country is not None:
            products_by_country[country].append(prod)
    return all_products, products_by_country

# Global variables for product catalog (will be set during training)
ALL_PRODUCTS = None
PRODUCTS_BY_COUNTRY = None

# =============================================================================
# Negative Sampling Stream
# =============================================================================
def df_to_stream_with_negative_sampling(df, negative_ratio=2):
    # Drop identifier columns that are not used as features.
    drop_cols = ['ClientID', 'StoreID']
    df = df.drop(columns=drop_cols, errors='ignore')
    for _, row in df.iterrows():
        pos_example = row.to_dict()
        if 'TransactionDate' in pos_example and hasattr(pos_example['TransactionDate'], 'isoformat'):
            pos_example['TransactionDate'] = pos_example['TransactionDate'].isoformat()
        yield pos_example, 1
        client_country = row.get('ClientCountry', None)
        if client_country is None:
            continue
        candidates = PRODUCTS_BY_COUNTRY.get(client_country, [])
        if not candidates:
            continue
        pos_product_id = row.get('ProductID', None)
        candidate_negatives = [prod for prod in candidates if prod.get('ProductID') != pos_product_id]
        if not candidate_negatives:
            candidate_negatives = candidates
        for _ in range(negative_ratio):
            neg_product = random.choice(candidate_negatives)
            neg_example = row.to_dict()
            for col in product_cols:
                if col in neg_product:
                    neg_example[col] = neg_product[col]
            neg_example['Quantity_sold'] = 0
            neg_example['SalesNetAmountEuro'] = 0
            yield neg_example, 0

# =============================================================================
# Helper Functions for Recommendation
# =============================================================================
def fill_missing_features(client_features, default_values):
    for key, default in default_values.items():
        if key not in client_features:
            client_features[key] = default
    return client_features

def recommend_for_client(client_features, available_products, model_pipeline, top_k=5):
    client_features = fill_missing_features(client_features, default_values)
    scores = []
    for product in available_products:
        x = {**client_features, **product}
        prob = model_pipeline.predict_proba_one(x).get(1, 0)
        product_id = product.get('ProductID', None)
        scores.append((product_id, prob))
    scores.sort(key=lambda tup: tup[1], reverse=True)
    return scores[:top_k]

def clean_client_features(row, keys_to_drop=None):
    client_features = row.to_dict()
    if keys_to_drop is None:
        keys_to_drop = ['ProductID', 'Quantity_sold', 'SalesNetAmountEuro',
                        'Category', 'FamilyLevel1', 'FamilyLevel2', 'Universe', 'Brand']
    for key in keys_to_drop:
        client_features.pop(key, None)
    return client_features

# =============================================================================
# Training Function
# =============================================================================
def train_model(data_path=DATA_PATH, negative_ratio=2, model_save_path='pipeline_arf.pkl'):
    data = load_data(data_path)
    # Split data chronologically: 80% train, 20% test.
    train_size = int(0.8 * len(data))
    df_train = data.iloc[:train_size]
    # Build global product catalog.
    global ALL_PRODUCTS, PRODUCTS_BY_COUNTRY
    ALL_PRODUCTS, PRODUCTS_BY_COUNTRY = build_product_catalog(data)
    train_stream = df_to_stream_with_negative_sampling(df_train, negative_ratio=negative_ratio)
    # Train the ARF pipeline.
    for i, (x, y) in enumerate(train_stream):
        if i % 1000 == 0:
            print(f"Training iteration {i}")
        pipeline_arf.learn_one(x, y)
    # Save the trained model.
    with open(model_save_path, 'wb') as f:
        pickle.dump(pipeline_arf, f)
    print("Training complete. Model saved to", model_save_path)
    return

# =============================================================================
# Load Model Function
# =============================================================================
def load_model(model_path='pipeline_arf.pkl'):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

# =============================================================================
# Evaluation on a Specific Test Row
# =============================================================================
def evaluate_on_row(row, model, top_k=100):
    ground_truth = row.get('ProductID')
    client_features = clean_client_features(row)
    client_country = client_features.get('ClientCountry', default_values['ClientCountry'])
    candidates = [prod for prod in ALL_PRODUCTS if prod.get('StoreCountry') == client_country]
    recommendations = recommend_for_client(client_features, candidates, model, top_k=top_k)
    recommended_ids = [prod_id for prod_id, prob in recommendations]
    hit = 1 if ground_truth in recommended_ids else 0
    return hit, recommendations

# =============================================================================
# Recommendation for a Given Customer ID
# =============================================================================
def recommend_for_customer(customer_id, model, top_k=5):
    data = load_data(DATA_PATH)
    customer_rows = data[data['ClientID'] == customer_id]
    if customer_rows.empty:
        print(f"No data found for customer {customer_id}")
        return []
    # Use the first occurrence.
    row = customer_rows.iloc[0]
    client_features = clean_client_features(row)
    client_country = client_features.get('ClientCountry', default_values['ClientCountry'])
    candidates = [prod for prod in ALL_PRODUCTS if prod.get('StoreCountry') == client_country]
    recommendations = recommend_for_client(client_features, candidates, model, top_k=top_k)
    return recommendations

# =============================================================================
# Main Block: Command-line Interface
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and evaluate the recommendation system.")
    parser.add_argument("--train", action="store_true", help="Train the model")
    parser.add_argument("--model_path", type=str, default="pipeline_arf.pkl", help="Path to save/load the model")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate model on a specific test row (by index)")
    parser.add_argument("--row_index", type=int, default=0, help="Row index from test set to evaluate on")
    parser.add_argument("--recommend", type=str, help="Customer ID to create recommendations for")
    args = parser.parse_args()
    
    if args.train:
        print("Training model...")
        train_model(data_path=DATA_PATH, negative_ratio=2, model_save_path=args.model_path)
        print("Model trained.")
    
    model = load_model(args.model_path)
    
    if args.evaluate:
        data = load_data(DATA_PATH)
        train_size = int(0.8 * len(data))
        df_test = data.iloc[train_size:]
        row = df_test.iloc[args.row_index]
        hit, recs = evaluate_on_row(row, model, top_k=100)
        print(f"Evaluation on row {args.row_index}: Hit = {hit}")
        print("Recommendations:")
        for prod_id, prob in recs:
            print(f"Product: {prod_id} - Probability: {prob:.4f}")
    
    if args.recommend:
        recs = recommend_for_customer(args.recommend, model, top_k=5)
        print(f"Recommendations for customer {args.recommend}:")
        for prod_id, prob in recs:
            print(f"Product: {prod_id} - Probability: {prob:.4f}")