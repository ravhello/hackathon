import pandas as pd
from models.recommender import LightFMRecommender
import pickle

# Load data
df = pd.read_parquet("../final_df.parquet")

# Initialize and train recommender
recommender = LightFMRecommender(df)
recommender.fit_model(epochs=30, num_threads=8)

# Important: set the module name to match where the class will be imported from
recommender.__module__ = 'models.recommender'

# Save the model
with open('recommender.pkl', 'wb') as f:
    pickle.dump(recommender, f)