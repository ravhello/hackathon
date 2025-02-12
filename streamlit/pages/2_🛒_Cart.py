import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import utils

def get_frequently_bought_together(df, product_ids, n_recommendations=5):
    if df.empty or not product_ids:
        return pd.DataFrame()
        
    # Group transactions by ClientID and TransactionDate to get transaction groups
    df['TransactionGroup'] = df.groupby(['ClientID', 'TransactionDate']).ngroup()
    
    # Get transactions containing any of the cart products
    relevant_transactions = df[df['ProductID'].isin(product_ids)]
    
    if relevant_transactions.empty:
        return pd.DataFrame()
    
    # Get all products from these transactions except the ones already in cart
    related_products = df[
        (df['TransactionGroup'].isin(relevant_transactions['TransactionGroup'])) &
        (~df['ProductID'].isin(product_ids))
    ]
    
    if related_products.empty:
        return pd.DataFrame()
    
    # Group by product and calculate frequency
    product_frequency = related_products.groupby('ProductID').agg({
        'Quantity_sold': 'sum',
        'avg_price': 'first',
        'Universe': 'first',
        'Category': 'first',
        'FamilyLevel1': 'first',
        'FamilyLevel2': 'first'
    }).reset_index()
    
    # Normalize frequency scores
    scaler = MinMaxScaler()
    product_frequency['frequency_score'] = scaler.fit_transform(
        product_frequency[['Quantity_sold']]
    )
    
    return product_frequency.nlargest(n_recommendations, 'frequency_score')

def display_recommendations(recommendations):
    if recommendations.empty:
        st.info("Pas de recommandations disponibles")
        return
        
    st.subheader("Fréquemment achetés ensemble")
    cols = st.columns(5)
    for idx, (_, product) in enumerate(recommendations.iterrows()):
        with cols[idx]:
            st.write(f"**{product['FamilyLevel2']}**")
            st.write(f"{product['Category']} | {product['Universe']}")
            st.write(f"Prix: {product['avg_price']:.2f}€")
            if st.button("🛒", key=f"rec_add_{product['ProductID']}"):
                if 'cart' not in st.session_state:
                    st.session_state.cart = []
                st.session_state.cart.append({
                    'id': product['ProductID'],
                    'name': product['FamilyLevel2'],
                    'price': product['avg_price']
                })
                st.rerun()


def main():
    if not st.session_state.get('logged_in', False):
        st.error("Please vous connecter pour accéder au panier")
        return
        
    st.title("🛒 Cart")
    
    if not st.session_state.get('cart', []):
        st.write("Votre panier est vide!")
        return
        
    # Load data
    df = utils.load_data()
    
    if df.empty:
        st.error("Impossible de charger les données")
        return
    
    # Display cart contents in main area
    st.subheader("Contenu de votre panier")
    
    total = 0
    for item in st.session_state.cart:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{item['name']}**")
        with col2:
            st.write(f"{item['price']:.2f}€")
        with col3:
            if st.button("🗑️", key=f"main_remove_{item['id']}"):
                st.session_state.cart.remove(item)
                st.rerun()
        total += item['price']
    
    st.write("---")
    st.write(f"**Total: {total:.2f}€**")
    
    # Add recommendations
    product_ids = [item['id'] for item in st.session_state.cart]
    recommendations = get_frequently_bought_together(df, product_ids)
    display_recommendations(recommendations)
    
    # Checkout button
    if st.button("Procéder au paiement"):
        # Add payment processing logic here
        st.success("Commande validée! Merci de votre achat.")
        st.session_state.cart = []
        st.rerun()

if __name__ == "__main__":
    main()