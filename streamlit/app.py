import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler

# Configuration de la page
st.set_page_config(
    page_title="Sport Marketplace",
    page_icon="🏃",
    layout="wide"
)

# Chargement des données
@st.cache_data
def load_data():
    df = pd.read_csv('data.csv')
    df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
    return df

# Fonction pour obtenir les recommandations
def get_recommendations(df, user_age, user_gender, user_country, n_recommendations=20):
    # Calcul du score basé sur plusieurs facteurs
    product_metrics = df.groupby('ProductID').agg({
        'Quantity_sold': 'sum',
        'SalesNetAmountEuro': 'sum',
        'avg_price': 'first',
        'Universe': 'first',
        'Category': 'first',
        'FamilyLevel1': 'first',
        'FamilyLevel2': 'first'
    }).reset_index()
    
    # Score de vente
    scaler = MinMaxScaler()
    product_metrics['sales_score'] = scaler.fit_transform(
        product_metrics[['Quantity_sold']]
    )
    
    # Score de prix (plus le prix est proche de la moyenne, plus le score est élevé)
    mean_price = product_metrics['avg_price'].mean()
    product_metrics['price_diff'] = abs(product_metrics['avg_price'] - mean_price)
    product_metrics['price_score'] = 1 - scaler.fit_transform(
        product_metrics[['price_diff']]
    )
    
    # Score démographique
    demographic_df = df[
        (df['ClientGender'] == user_gender) &
        (df['StoreCountry'] == user_country) &
        (df['AgeGroup'] == f"{(user_age//10)*10}-{(user_age//10)*10+10}")
    ]
    
    if not demographic_df.empty:
        demographic_metrics = demographic_df.groupby('ProductID')['Quantity_sold'].sum().reset_index()
        demographic_metrics['demographic_score'] = scaler.fit_transform(
            demographic_metrics[['Quantity_sold']]
        )
        product_metrics = product_metrics.merge(
            demographic_metrics[['ProductID', 'demographic_score']],
            on='ProductID',
            how='left'
        )
    else:
        product_metrics['demographic_score'] = 0
    
    product_metrics['demographic_score'] = product_metrics['demographic_score'].fillna(0)
    
    # Score final combiné
    product_metrics['final_score'] = (
        0.4 * product_metrics['sales_score'] +
        0.3 * product_metrics['price_score'] +
        0.3 * product_metrics['demographic_score']
    )
    
    # Sélection des meilleurs produits
    top_products = product_metrics.nlargest(n_recommendations, 'final_score')
    
    return df[df['ProductID'].isin(top_products['ProductID'])].drop_duplicates('ProductID')

# Classe pour gérer les utilisateurs
class UserManager:
    def __init__(self):
        self.users = pd.DataFrame(columns=['UserID', 'Email', 'Password', 'Age', 'Gender', 'Country'])
        
    def add_user(self, email, password, age, gender, country):
        user_id = len(self.users) + 1
        new_user = pd.DataFrame({
            'UserID': [user_id],
            'Email': [email],
            'Password': [password],
            'Age': [age],
            'Gender': [gender],
            'Country': [country]
        })
        self.users = pd.concat([self.users, new_user], ignore_index=True)
        return user_id

    def verify_user(self, email, password):
        user = self.users[
            (self.users['Email'] == email) & 
            (self.users['Password'] == password)
        ]
        if not user.empty:
            return user.iloc[0]
        return None

# Initialisation des variables de session
if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserManager()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'cart' not in st.session_state:
    st.session_state.cart = []

def registration_page():
    st.title("👤 Compte Utilisateur")
    
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter")
            
            if submitted:
                user = st.session_state.user_manager.verify_user(email, password)
                if user is not None:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user
                    st.success("Connexion réussie!")
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect")
    
    with tab2:
        with st.form("registration_form"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            age = st.number_input("Âge", min_value=18, max_value=100)
            gender = st.selectbox("Genre", ["M", "F"])
            country = st.selectbox("Pays", ["FRA", "GBR", "USA"])
            submitted = st.form_submit_button("S'inscrire")
            
            if submitted:
                st.session_state.user_manager.add_user(email, password, age, gender, country)
                st.success("Inscription réussie! Vous pouvez maintenant vous connecter.")

def recommendations_page():
    st.title("🛍️ Recommandations Personnalisées")
    
    user = st.session_state.user_data
    df = load_data()
    
    # Obtention des recommandations
    recommended_products = get_recommendations(
        df,
        user['Age'],
        user['Gender'],
        user['Country']
    )
    
    # Filtres et tri
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_universe = st.selectbox(
            "Univers", 
            ['Tous'] + list(recommended_products['Universe'].unique())
        )
    with col2:
        selected_category = st.selectbox(
            "Catégorie", 
            ['Tous'] + list(recommended_products['Category'].unique())
        )
    with col3:
        sort_by = st.selectbox(
            "Trier par",
            ['Prix croissant', 'Prix décroissant', 'Popularité']
        )
    
    # Application des filtres
    filtered_products = recommended_products.copy()
    if selected_universe != 'Tous':
        filtered_products = filtered_products[
            filtered_products['Universe'] == selected_universe
        ]
    if selected_category != 'Tous':
        filtered_products = filtered_products[
            filtered_products['Category'] == selected_category
        ]
    
    # Tri des produits
    if sort_by == 'Prix croissant':
        filtered_products = filtered_products.sort_values('avg_price')
    elif sort_by == 'Prix décroissant':
        filtered_products = filtered_products.sort_values('avg_price', ascending=False)
    elif sort_by == 'Popularité':
        filtered_products = filtered_products.sort_values('Quantity_sold', ascending=False)
    
    # Affichage des produits
    st.subheader(f"Produits recommandés pour vous ({len(filtered_products)} produits)")
    
    for idx, row in filtered_products.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['FamilyLevel2']}**")
                st.write(f"{row['Category']} | {row['Universe']} | {row['FamilyLevel1']}")
            with col2:
                st.write(f"Prix moyen: {row['avg_price']:.2f}€")
            with col3:
                if st.button("Ajouter au panier", key=f"add_{row['ProductID']}"):
                    st.session_state.cart.append({
                        'product_id': row['ProductID'],
                        'name': row['FamilyLevel2'],
                        'price': row['avg_price']
                    })
                    st.success("Produit ajouté au panier!")
    
    # Panier dans la sidebar
    st.sidebar.title("🛒 Mon Panier")
    total = 0
    for item in st.session_state.cart:
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.write(item['name'])
        with col2:
            st.write(f"{item['price']:.2f}€")
        total += item['price']
    
    st.sidebar.write("---")
    st.sidebar.write(f"**Total: {total:.2f}€**")
    
    if st.sidebar.button("Passer la commande"):
        if len(st.session_state.cart) > 0:
            st.sidebar.success("Commande validée!")
            st.session_state.cart = []
        else:
            st.sidebar.error("Votre panier est vide")

def main():
    if not st.session_state.logged_in:
        registration_page()
    else:
        recommendations_page()

if __name__ == "__main__":
    main()