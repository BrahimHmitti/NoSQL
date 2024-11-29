# 🕵️‍♂️ Détecteur de Corruption v1.0

## Marre des petits malins qui se sucrent sur le dos de la République? 

Vous vous demandez comment votre voisin peut s'offrir une Porsche avec un salaire de fonctionnaire? Notre IA va mettre son nez dans leurs affaires! 🔍

### 🎯 Ce que fait notre mouchard digital

- Analyse le train de vie suspect de nos chers "serviteurs de l'État"
- Compare leurs revenus déclarés avec leurs dépenses fastueuses 
- Calcule un pourcentage de risque de corruption
- Stocke les analyses dans MongoDB (parce qu'on n'oublie rien!)
- Compte les analyses effectuées avec Redis (pour le plaisir des statistiques)

### 🛠️ Installation

```bash
# Clonez ce dépôt de justice
git clone https://github.com/BrahimHmitti/NoSQL.git

# Changez de branche vers version-docker-local, cette branch est pour tester localement avec docker , la branche main est pour le deploment en ligne sur google cloud.
git checkout version-docker-local

### 🔑 Configuration

Créez un fichier 

.env

 avec votre clé API Google Gemini:
```properties
GOOGLE_API_KEY=votre_clé_secrète_ici
**Pour mon prof je vous ai envoyé ma clé par mail**

# Installez les dépendances 
docker compose up --build
```


```

### 🎮 Utilisation

1. Ouvrez `http://localhost:5000`
2. Entrez les informations du suspect
3. Laissez l'IA faire son enquête
4. Découvrez la vérité! 

### ⚠️ Avertissement

Ce projet est destiné à des fins éducatives uniquement. Nous ne sommes pas responsables si vous découvrez que votre maire se fait livrer des lingots d'or par drone.

### 🤝 Contribution

Les PRs sont les bienvenues! Ensemble, luttons contre la corruption avec humour et technologie.

---

*Parce que la transparence, c'est comme le café : meilleure servie chaude et sans sucre ajouté! ☕*
