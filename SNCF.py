import streamlit as st
import folium
import pandas as pd
import json
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import plotly.express as px
import os
import matplotlib.pyplot as plt
import plotly.graph_objs as go

st.set_page_config(layout="wide")
st.sidebar.image("image.png")


# Configuration de la barre latérale pour la navigation
page = st.sidebar.selectbox("Aller à", ["Fréquentation des gares en France", "Carte Interactive", "Évolution de la Qualité de l'Air", "Impact sur la Santé Publique"])



# Page d'accueil
if page == "Évolution de la Qualité de l'Air":

    sub_page = st.sidebar.selectbox(" ", ["Concentrations de polluants atmosphériques", "Empreintes CO2 par mode de transport"])

    # Page d'accueil
    if sub_page == "Concentrations de polluants atmosphériques":

        # Chargement des données depuis le fichier CSV
        @st.cache_data
        def load_data():
            qualite_ineris = pd.read_csv('data/qualite_ineris.csv', sep=';')
            return qualite_ineris

        # Chargement des données
        qualite_ineris = load_data()

        # Titre de l'application
        st.title('Données de mesure des concentrations de polluants atmosphériques')

        # PREVISONS 
        # Renommer les colonnes pour être compatibles avec la moyenne mobile
        qualite_ineris['ds'] = qualite_ineris['Date']
        qualite_ineris['y'] = qualite_ineris['valeur brute']

        # Initialiser un DataFrame pour stocker les prévisions de chaque code site
        toutes_les_previsions = pd.DataFrame()

        # Parcourir chaque code site unique
        for code_site in qualite_ineris['code site'].unique():
            # Filtrer les données pour le code site actuel
            donnees_site = qualite_ineris[qualite_ineris['code site'] == code_site]

            # Calculer la moyenne mobile d'ordre 7
            donnees_site['moyenne_mobile'] = donnees_site['y'].rolling(window=7, min_periods=7).mean()

            # Créer un DataFrame pour les 7 prochains jours
            future = pd.DataFrame({'ds': pd.date_range(start='2024-01-16', end='2024-01-22')})

            # Utiliser la dernière valeur de la moyenne mobile comme prévision pour les 7 prochains jours
            derniere_moyenne_mobile = donnees_site['moyenne_mobile'].iloc[-1]
            previsions = pd.DataFrame({'Date': future['ds'], 'nom site': donnees_site['nom site'] , 'code site': code_site, 'yhat': derniere_moyenne_mobile})

            # Ajouter les prévisions du code site actuel au DataFrame global
            toutes_les_previsions = pd.concat([toutes_les_previsions, previsions[['code site', 'nom site', 'Date', 'yhat']]])


        # Sidebar pour la sélection des municipalités
        selected_municipalities = st.sidebar.multiselect('Sélectionnez un site ou plusieurs sites', qualite_ineris['nom site'].unique())

        # Filtrer les données en fonction des municipalités sélectionnées
        filtered_df = qualite_ineris[qualite_ineris['nom site'].isin(selected_municipalities)]
        filtered_prev = toutes_les_previsions[toutes_les_previsions['nom site'].isin(selected_municipalities)]
        champs_filtered = ['Date','nom site','valeur brute','Name','Municipality','Latitude','Longitude','Altitude']
        # Afficher les données filtrées
        st.write('### Données pour les sites sélectionnés:')
        st.dataframe(filtered_df[champs_filtered], hide_index=True, width=1350)

        # Tracer l'évolution moyenne des valeurs par jour
        # Tracer l'évolution moyenne des valeurs par jour
        for selected_municipality in selected_municipalities:
            municipality_data = filtered_df[filtered_df['nom site'] == selected_municipality]
            municipality_data = municipality_data.sort_values(by='Date')

            # Création du graphique avec Plotly Express
            fig = px.line(municipality_data, x='Date', y='valeur brute',
                        title=f'Évolution de la valeur brute pour {selected_municipality}',
                        labels={'Date': 'Date', 'valeur brute': 'Valeur brute'},
                        markers=True)

            # Afficher le graphique avec st.write()
            # st.write(fig)

            # Personnalisation supplémentaire (si nécessaire)
            fig.update_layout(xaxis_tickangle=-45, width=1350, height=600)

            # Affichage du graphique
            st.plotly_chart(fig)
    
    # Page d'accueil
    if sub_page == "Empreintes CO2 par mode de transport":

        # Chargement des données depuis le fichier CSV
        @st.cache_data
        def load_data():
            data = pd.read_csv('data/emission-co2-tgv.csv', sep=';')
            return data

        # Chargement des données
        data = load_data()

        # Titre de l'application
        st.title('Comparaisons des empreintes CO2 par mode de transport')

        # Recherche de gares
        # Create a filter for the manufacturer
        col = "Origine"
        unique_mnfr = sorted(data['Origine'].unique())
        filter_1 = st.sidebar.multiselect(f"Selectionnez {col}", unique_mnfr)
        mask_1 = data['Origine'].isin(filter_1 or unique_mnfr)

        # Create a filter for the Model Number
        col = "Destination"
        unique_models = sorted(data[mask_1][col].unique())
        filter_2 = st.sidebar.multiselect(f"Selectionnez {col}", unique_models)
        mask_2 = data[mask_1][col].isin(filter_2 or unique_models)

        final_mask = mask_1 & mask_2
        filtered_data = data[final_mask].copy()
        mes_champs = ['Liaison','Distance (km)','TGV (1 pers.) - Empreinte CO2e (kgCO2e/voyageur)','Voiture (autosolisme 1 pers.) - Empreinte CO2e (kgCO2e/voyageur)','Voiture (covoiturage 3 pers.) - Empreinte CO2e (kgCO2e/voyageur)']
        #st.dataframe(filtered_data[mes_champs], hide_index = True)
        # Affichage des données de fréquentation pour les gares sélectionnées
        if not filtered_data.empty:
            st.subheader('Données de Co2 pour les déplacements sélectionnés')
            st.dataframe(filtered_data[mes_champs], hide_index=True)
            
            # Création du graphique pour les déplacements sélectionnés
            #for selected_origine in mask1:
            #    gare_data = selected_data[selected_data['Nom de la gare'] == selected_gare]
        # Création du graphique empilé pour les déplacements sélectionnés
            # Création du graphique empilé pour les déplacements sélectionnés
            if (filtered_data['Liaison'].nunique() <= 15):
                # Préparation des données pour Plotly Express
                df_stacked = filtered_data.melt(id_vars=['Liaison'], 
                                                value_vars=['TGV (1 pers.) - Empreinte CO2e (kgCO2e/voyageur)', 
                                                            'Voiture (autosolisme 1 pers.) - Empreinte CO2e (kgCO2e/voyageur)', 
                                                            'Voiture (covoiturage 3 pers.) - Empreinte CO2e (kgCO2e/voyageur)'],
                                                var_name='Mode de Transport', 
                                                value_name='Empreinte CO2e')

                # Création du graphique empilé avec Plotly Express
                fig = px.bar(df_stacked, x='Liaison', y='Empreinte CO2e', 
                            color='Mode de Transport', 
                            title='Empreinte CO2e pour les déplacements sélectionnés')

                # Personnalisation supplémentaire (si nécessaire)
                fig.update_layout(xaxis_tickangle=-45, width=1350, height=600)
                fig.update_traces(texttemplate='%{y:.2f}', textposition='inside')

                # Affichage du graphique
                st.plotly_chart(fig)
            else:
                st.warning('Trop de déplacements sélectionnés (15 destinations au plus)')

# Page d'accueil
if page == "Fréquentation des gares en France":


    # Chargement des données depuis le fichier CSV
    @st.cache_data
    def load_data():
        data = pd.read_csv('data/frequentation-gares.csv', sep=';', encoding='ISO-8859-1')
        return data

    # Chargement des données
    data = load_data()

    # Titre de l'application
    st.title('Fréquentation des gares en France')

    # Recherche de gares
    selected_gares = st.multiselect('Rechercher une gare :', options=data['Nom de la gare'].unique())

    # Filtrer les données en fonction des gares sélectionnées
    selected_data = data[data['Nom de la gare'].isin(selected_gares)]

    # Affichage des données de fréquentation pour les gares sélectionnées
    if not selected_data.empty:
        st.subheader('Données de fréquentation pour les gares sélectionnées')
        st.dataframe(selected_data, hide_index=True)
        
        # Création du graphique pour chaque gare sélectionnée
        for selected_gare in selected_gares:
            gare_data = selected_data[selected_data['Nom de la gare'] == selected_gare]
            years = [str(year) for year in range(2015, 2023)]
            values = [gare_data[f'Total Voyageurs {year}'].values[0] for year in years]

            fig = px.bar(x=years, y=values, labels={'x': 'Année', 'y': 'Nombre de voyageurs'},
                        title=f'Fréquentation de {selected_gare} par année')
            fig.update_layout(xaxis_tickangle=-45)
            # Personnaliser les dimensions du graphique
            fig.update_layout(width=1350, height=500)

            # Afficher le graphique avec st.write()
            st.write(fig)
    else:
        st.warning('Aucune donnée disponible pour les gares sélectionnées.')





# Page d'accueil
if page == "Carte Interactive":

    # Configuration de la barre latérale pour la navigation
    # st.sidebar.title("Choix du marqueur")
    marker = st.sidebar.selectbox("", ["Gares", "Vélos"])

    st.sidebar.write("""
        **Échelle de Qualité de l'Air Basée sur le Niveau de NO2 :**

        - **Très Bas [Bleu Clair]** : 4-6 : Niveau très faible de pollution, considéré comme non problématique pour la santé.

        - **Bas [Bleu]** : 6-8 : Niveau bas de pollution, sans risque significatif pour la santé.

        - **Modéré [Vert]** : 8-10 : Niveau modéré de pollution. Peut commencer à affecter les personnes sensibles.

        - **Élevé [Jaune]** : 10-12 : Niveau élevé de pollution. Risque accru pour les groupes sensibles.

        - **Très Élevé [Orange]** : 12-14 : Qualité de l'air mauvaise. Effets sur la santé possibles même pour les personnes en bonne santé.

        - **Dangereux [Rouge]** : 14-17 : Niveau dangereux de pollution. Effets sur la santé graves possibles pour tout le monde.
        """)


    # Charger les données
    pollution_df = pd.read_csv('data/citeair.csv', sep=';')

    # Charger les données
    gares_df = pd.read_csv('data/emplacement-des-gares-idf.csv', sep=';')
    data_filtrée = pd.read_csv("data/amenagements-velo-en-ile-de-france_limited.csv", sep=',')

    # if marker == "Vélos":
    #     # Création de la liste des valeurs uniques de 'code_post'
    #     liste_code_post = velo_df['Departement'].unique()
# 
    #     # Utiliser une boîte de sélection pour demander à l'utilisateur de choisir une valeur de code_post
    #     code_post_choisi = st.selectbox("Veuillez choisir une valeur de département à filtrer :", liste_code_post)
# 
    #     # Filtrer les données en fonction de la sélection de l'utilisateur
    #     data_filtrée = velo_df[velo_df['Departement'] == code_post_choisi]

    

    # Extrait les coordonnées et calcule la moyenne pour le point de départ de la carte
    coords = gares_df['Geo Point'].str.split(',', expand=True).astype(float)
    latitude_moyenne = coords[0].mean()
    longitude_moyenne = coords[1].mean()

    st.title("Carte Interactive")

    # Créer la carte de base
    ma_carte = folium.Map(location=[48.8566, 2.3522], zoom_start=10)

    def couleur_selon_no2(valeur_no2):
        if 4 <= valeur_no2 <= 6:
            return '#6fa8dc'  # Bleu Clair pour Très Bas
        elif 6 < valeur_no2 <= 8:
            return '#2986cc'  # Bleu pour Bas 
        elif 8 < valeur_no2 <= 10:
            return '#8fce00'  # Vert pour Modéré
        elif 10 < valeur_no2 <= 12:
            return '#ffd966'  # Jaune pour Élevé
        elif 12 < valeur_no2 <= 14:
            return '#e69138'  # Orange pour Très Élevé
        else:  # 14 < valeur_no2 <= 17
            return '#e06666'  # Rouge pour Dangereux



    # Ajouter les polygones à la carte
    for index, row in pollution_df.iterrows():
        # Assurez-vous que la colonne 'geom' est au format JSON valide
        polygone_geojson = json.loads(row['geom'])
        
        # Utilisez la fonction de couleur selon la valeur de NO2
        couleur = couleur_selon_no2(row['NO2'])
        
        folium.GeoJson(
            polygone_geojson,
            style_function=lambda x, couleur=couleur: {
                'fillColor': couleur,
                'color': couleur,
                'weight': 2,
                'fillOpacity': 0.6
            }
        ).add_to(ma_carte)


    # Créer une instance de MarkerCluster
    marker_cluster = MarkerCluster().add_to(ma_carte)

    if marker == "Gares":
        # Ajouter les marqueurs de gares
        for _, row in gares_df.iterrows():
            coord = tuple(map(float, row['Geo Point'].split(',')))
            folium.Marker(
                location=coord,
                popup=f"{row['nom_long']}",
                tooltip=row['nom_long'], 
                icon=folium.Icon(icon='train', prefix='fa')
            ).add_to(marker_cluster)
        
        # Créer une instance de MarkerCluster
        marker_cluster = MarkerCluster().add_to(ma_carte)
    
    if marker == "Vélos":
        # Ajout des marqueurs au cluster
        for _, row in data_filtrée.iterrows():
            coord = tuple(map(float, row['geo_point_2d'].split(',')))
            
            folium.Marker(
                location=coord,
                popup=f"{row['nom_voie']}<br>Type de voie: {row['highway']}<br>Revêtement: {row['revetement']}",
                tooltip=row['nom_voie'],
                icon=folium.Icon(icon='bicycle', prefix='fa')
            ).add_to(marker_cluster)
        
        # Créer une instance de MarkerCluster
        marker_cluster = MarkerCluster().add_to(ma_carte)


    # Afficher la carte
    folium_static(ma_carte, width=1350, height=800) 


# Page d'accueil
if page == "Impact sur la Santé Publique":
    st.title("Impact sur la Santé Publique")

    # Initialize showing_cars in session state
    if 'showing_cars' not in st.session_state:
        st.session_state.showing_cars = True

    # Load data
    df_voitures = pd.read_csv("data/mars-2014-complete.csv", sep=";", encoding="latin1")
    df_transports = pd.read_csv("data/emission-de-co2e-par-voyageur-kilometre-sur-le-reseau.csv", sep=";", engine='python')

    average_voitures = df_voitures.groupby('Carrosserie')['co2'].mean().reset_index()
    average_transports = df_transports.groupby('LineMode')['CO2e/voy/km'].mean().reset_index()

    # Create bar charts with rounded values displayed on bars
    fig_voitures = px.bar(average_voitures, x='Carrosserie', y='co2', color='Carrosserie',
                        text=average_voitures['co2'].round(1).astype(str),  # Display rounded values on top of the bars
                        labels={'co2': 'Consommation moyenne (L/100km)'},
                        title='Consommation moyenne par carrosserie de voiture')
    fig_voitures.update_layout(xaxis={'categoryorder': 'total descending'})

    fig_transports = px.bar(average_transports, x='LineMode', y='CO2e/voy/km', color="LineMode",
                            text=average_transports['CO2e/voy/km'].round(1).astype(str),  # Display rounded values on top of the bars
                            labels={'CO2e/voy/km': 'Consommation moyenne (g/km)'},
                            title='Consommation moyenne par moyen de transport')
    fig_transports.update_layout(xaxis={'categoryorder': 'total descending'})

    # Combine the two bar charts into a single chart with a separation
    fig_combined = go.Figure()

    # Add traces for car models
    fig_combined.add_trace(go.Bar(x=average_voitures['Carrosserie'], y=average_voitures['co2'],
                                marker_color=px.colors.qualitative.Plotly[0],
                                text=average_voitures['co2'].round(1).astype(str),
                                name='Consommation moyenne par carrosserie de voiture'))

    # Add traces for transport modes
    fig_combined.add_trace(go.Bar(x=average_transports['LineMode'], y=average_transports['CO2e/voy/km'],
                                marker_color=px.colors.qualitative.Plotly[1],
                                text=average_transports['CO2e/voy/km'].round(1).astype(str),
                                name='Consommation moyenne par moyen de transport'))

    # Update layout
    fig_combined.update_layout(barmode='group', xaxis={'categoryorder': 'total descending'},
                            title='Consommation moyenne par carrosserie de voiture et moyen de transport',
                            showlegend=True)
    
    # Personnalisation supplémentaire (si nécessaire)
    fig_combined.update_layout(width=1350, height=600)

    # Toggle between charts
    if st.button("Basculer entre les graphiques"):
        st.session_state.showing_cars = not st.session_state.showing_cars

    # Display the appropriate chart based on session state
    if st.session_state.showing_cars:
        st.plotly_chart(fig_combined)
    else:
        st.plotly_chart(fig_transports)
