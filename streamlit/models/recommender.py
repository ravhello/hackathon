#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
recommender.py - A LightFM-based recommendation system
"""

import numpy as np
import pandas as pd
from scipy.sparse import lil_matrix
from lightfm import LightFM
from lightfm.data import Dataset

class LightFMRecommender:
    """
    A hybrid recommendation system using LightFM that handles both collaborative filtering 
    and content-based features.
    """
    
    def __init__(self, df, 
                 user_feature_columns=[
                     "Age", 
                     "ClientGender", 
                     "ClientSegment", 
                     "ClientCountry",
                     "ClientOptINEmail",
                     "ClientOptINPhone"
                 ],
                 item_feature_columns=[
                     "Category", 
                     "FamilyLevel1", 
                     "FamilyLevel2", 
                     "Universe", 
                     "Brand",
                     "SalesNetAmountEuro",
                     "product_avg_price_order",
                     "avg_price",
                     "AveragePrice",
                     "StoreCountry"
                 ]):
        """
        Initialize the recommender from a complete transaction DataFrame.

        Parameters:
            df (pd.DataFrame): Complete transaction data
            user_feature_columns (list): Columns to use for user features
            item_feature_columns (list): Columns to use for item features
        """
        self.full_df = df.copy()
        
        # Create ID mappings
        self.unique_users = self.full_df['ClientID'].unique()
        self.unique_items = self.full_df['ProductID'].unique()
        
        self.user_id_map = {id_: idx for idx, id_ in enumerate(self.unique_users)}
        self.item_id_map = {id_: idx for idx, id_ in enumerate(self.unique_items)}
        
        self.reverse_user_map = {v: k for k, v in self.user_id_map.items()}
        self.reverse_item_map = {v: k for k, v in self.item_id_map.items()}

        # Create interaction table
        self.interactions_df = (
            self.full_df.groupby(["ClientID", "ProductID"])
            .agg({"Quantity_sold": "sum"})
            .reset_index()
        )
        self.interactions_df["interaction"] = 1
        self.interactions_df['user_idx'] = self.interactions_df['ClientID'].map(self.user_id_map)
        self.interactions_df['item_idx'] = self.interactions_df['ProductID'].map(self.item_id_map)

        # Create feature DataFrames
        self.user_features_df = (
            self.full_df.groupby("ClientID")
            .first()
            .reset_index()[["ClientID"] + user_feature_columns]
        )
        self.user_features_df['user_idx'] = self.user_features_df['ClientID'].map(self.user_id_map)

        self.product_info_df = (
            self.full_df.groupby("ProductID")
            .first()
            .reset_index()[["ProductID"] + item_feature_columns]
        )
        self.product_info_df['item_idx'] = self.product_info_df['ProductID'].map(self.item_id_map)

        self.user_feature_columns = user_feature_columns
        self.item_feature_columns = item_feature_columns

        # Initialize LightFM dataset
        self.dataset = Dataset()
        
        # Prepare feature lists
        self.user_features = self._generate_user_features_list()
        self.item_features = self._generate_item_features_list()

        # Fit dataset
        self.dataset.fit(
            users=range(len(self.unique_users)),
            items=range(len(self.unique_items)),
            user_features=self.user_features,
            item_features=self.item_features
        )

        # Build matrices
        self._build_matrices()

        # Initialize model
        self.model = LightFM(loss='warp', random_state=42)
        
        # Compute popularity
        self.popularity = self._compute_popularity()

    def _generate_user_features_list(self):
        """Generate the list of all possible user features."""
        features = []
        for col in self.user_feature_columns:
            unique_vals = self.user_features_df[col].dropna().unique()
            features.extend([f"{col}_{val}" for val in unique_vals])
        return features

    def _generate_item_features_list(self):
        """Generate the list of all possible item features."""
        features = []
        for col in self.item_feature_columns:
            unique_vals = self.product_info_df[col].dropna().unique()
            features.extend([f"{col}_{val}" for val in unique_vals])
        return features

    def _build_matrices(self):
        """Build interaction and feature matrices for LightFM."""
        # Build interactions
        self.interactions = self.dataset.build_interactions(
            ((row.user_idx, row.item_idx, row.interaction) 
             for _, row in self.interactions_df.iterrows())
        )[0]

        # Build user features
        user_features_dict = {}
        for _, row in self.user_features_df.iterrows():
            features = []
            for col in self.user_feature_columns:
                if pd.notnull(row[col]):
                    features.append(f"{col}_{row[col]}")
            user_features_dict[row.user_idx] = features

        self.user_features_matrix = self.dataset.build_user_features(
            ((idx, feats) for idx, feats in user_features_dict.items()),
            normalize=False
        )

        # Build item features
        item_features_dict = {}
        for _, row in self.product_info_df.iterrows():
            features = []
            for col in self.item_feature_columns:
                if pd.notnull(row[col]):
                    features.append(f"{col}_{row[col]}")
            item_features_dict[row.item_idx] = features

        self.item_features_matrix = self.dataset.build_item_features(
            ((idx, feats) for idx, feats in item_features_dict.items()),
            normalize=False
        )

    def _compute_popularity(self):
        """Compute global item popularity."""
        pop = self.interactions_df.groupby("ProductID")["Quantity_sold"].sum().reset_index()
        pop["score"] = pop["Quantity_sold"] / pop["Quantity_sold"].max()
        return pop.sort_values("score", ascending=False).reset_index(drop=True)

    def fit_model(self, epochs=30, num_threads=4):
        """
        Train the LightFM model.

        Parameters:
            epochs (int): Number of training epochs
            num_threads (int): Number of threads to use for training
        """
        self.model.fit(
            self.interactions,
            user_features=self.user_features_matrix,
            item_features=self.item_features_matrix,
            epochs=epochs,
            num_threads=num_threads
        )
        print("Training completed.")

    def recommend_for_user(self, user_id, num_recommendations=10):
        """
        Generate recommendations for a user.

        Parameters:
            user_id: User identifier
            num_recommendations (int): Number of recommendations to generate

        Returns:
            pd.DataFrame: Recommendations with product IDs and scores
        """
        n_items = len(self.unique_items)

        if user_id in self.user_id_map:
            # Existing user
            user_idx = self.user_id_map[user_id]
            scores = self.model.predict(
                user_idx,
                np.arange(n_items),
                user_features=self.user_features_matrix,
                item_features=self.item_features_matrix
            )
        else:
            # New user with demo data
            user_row = self.user_features_df[self.user_features_df["ClientID"] == user_id]
            if not user_row.empty:
                features = []
                for col in self.user_feature_columns:
                    val = user_row.iloc[0][col]
                    if pd.notnull(val):
                        features.append(f"{col}_{val}")
                
                user_features = self.dataset.build_user_features([(0, features)], normalize=False)
                scores = self.model.predict(
                    0,
                    np.arange(n_items),
                    user_features=user_features,
                    item_features=self.item_features_matrix
                )
            else:
                # Completely unknown user
                return self.popularity.head(num_recommendations)

        # Sort scores and get recommendations
        top_items = np.argsort(-scores)[:num_recommendations]
        recommendations = pd.DataFrame({
            'ProductID': [self.reverse_item_map[idx] for idx in top_items],
            'score': scores[top_items]
        })
        
        return recommendations

    def get_item_details(self, product_ids):
        """
        Get detailed information about specific products.

        Parameters:
            product_ids: Single product ID or list of product IDs

        Returns:
            pd.DataFrame: Product details
        """
        if not isinstance(product_ids, (list, np.ndarray)):
            product_ids = [product_ids]
            
        return self.product_info_df[
            self.product_info_df['ProductID'].isin(product_ids)
        ].drop('item_idx', axis=1)