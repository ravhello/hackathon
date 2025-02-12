import streamlit as st
import pandas as pd
from utils import load_data, show_cart_sidebar
from sklearn.preprocessing import MinMaxScaler

# Page config
st.set_page_config(
    page_title="Sport Marketplace",
    page_icon="🏃",
    layout="wide"
)

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
    
    return product_metrics.nlargest(n_recommendations, 'popularity_score')

def get_personalized_recommendations(df, user_data, n_recommendations=12):
    if df.empty:
        return df
        
    # Add your personalization logic here
    # For now, return generic recommendations
    return get_generic_recommendations(df, n_recommendations)

def main():
    show_cart_sidebar()
    
    st.title("🏃 Sport Marketplace")
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.error("Impossible de charger les données")
        return
    
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        user = st.session_state.user_data
        st.write(f"Bienvenue {user['Email']}!")
        products = get_personalized_recommendations(df, user)
        st.subheader("Recommandations personnalisées pour vous")
    else:
        products = get_generic_recommendations(df)
        st.subheader("Produits populaires")
    
    # Display products in a grid
    if not products.empty:
        # Create a container for all products
        for idx, (_, product) in enumerate(products.iterrows()):
            if idx % 3 == 0:
                cols = st.columns(3)
            
            with cols[idx % 3]:
                st.write("---")
                st.write(f"**{product['FamilyLevel2']}**")
                st.write(f"{product['Category']} | {product['Universe']}")
                st.write(f"Prix: {product['avg_price']:.2f}€")
                
                if st.button("🛒", key=f"add_{product['ProductID']}"):
                    if 'cart' not in st.session_state:
                        st.session_state.cart = []
                    st.session_state.cart.append({
                        'id': product['ProductID'],
                        'name': product['FamilyLevel2'],
                        'price': product['avg_price']
                    })
                    st.rerun()
    else:
        st.warning("Aucun produit disponible pour le moment.")

if __name__ == "__main__":
    main()
