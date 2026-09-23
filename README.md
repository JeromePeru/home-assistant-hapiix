# Hapiix pour Home Assistant

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41BDF5?logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom%20Repository-41BDF5)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Intégration communautaire Home Assistant pour les comptes occupants Hapiix. Elle
permet de consulter les accès disponibles et d'envoyer une demande d'ouverture,
ainsi que d'afficher les membres et les messages reçus.

## Fonctionnalités

- authentification par adresse e-mail et code à usage unique ;
- renouvellement automatique du jeton d'accès ;
- création dynamique d'un bouton Home Assistant par porte ;
- récupération de toutes les portes visibles par le compte ;
- capteur du nombre de membres avec l'attribut `members` ;
- capteur des messages avec les attributs `unread` et `messages` ;
- actualisation automatique toutes les cinq minutes ;
- réauthentification depuis Home Assistant lorsque la session expire ;
- traductions française et anglaise.

## Avertissement important

Une pression sur un bouton de porte envoie une **véritable demande d'ouverture
physique**. Limitez l'accès au dashboard et ajoutez une confirmation à chaque
carte. N'exposez pas votre instance Home Assistant sans protections adaptées.

## Installation avec HACS

Ce dépôt peut être ajouté comme dépôt personnalisé :

1. Dans HACS, ouvrir **Intégrations**.
2. Ouvrir le menu ⋮ puis **Dépôts personnalisés**.
3. Ajouter `https://github.com/JeromePeru/home-assistant-hapiix`.
4. Choisir la catégorie **Intégration**.
5. Rechercher et télécharger **Hapiix**.
6. Redémarrer Home Assistant.

## Installation manuelle

1. Télécharger ce dépôt.
2. Copier `custom_components/hapiix` vers `/config/custom_components/hapiix`.
3. Vérifier que `/config/custom_components/hapiix/manifest.json` existe.
4. Redémarrer Home Assistant.

## Configuration

1. Ouvrir **Paramètres → Appareils et services**.
2. Cliquer sur **Ajouter une intégration** et rechercher **Hapiix**.
3. Saisir l'adresse e-mail enregistrée chez Hapiix.
4. Saisir le code à usage unique reçu par e-mail.
5. Attendre la première récupération des portes, membres et messages.

Les jetons sont conservés dans l'entrée de configuration Home Assistant. Ne
partagez jamais `/config/.storage/core.config_entries`.

## Entités créées

- `button.<nom_de_porte>` : envoie la demande d'ouverture ;
- `sensor.<compte>_members` : nombre de membres et attribut `members` ;
- `sensor.<compte>_messages` : nombre de messages, attributs `unread` et `messages`.

De nouvelles portes autorisées sur le compte produisent de nouvelles entités lors
d'une actualisation ultérieure.

## Carte de porte avec confirmation

Remplacez l'identifiant par celui de votre entité :

```yaml
type: button
entity: button.votre_porte_hapiix
name: Ouvrir la porte
icon: mdi:door-open
show_state: false
tap_action:
  action: perform-action
  perform_action: button.press
  target:
    entity_id: button.votre_porte_hapiix
  confirmation:
    title: Ouvrir cette porte ?
    text: Cette action envoie une demande d'ouverture physique à Hapiix.
    confirm_text: Ouvrir
    dismiss_text: Annuler
hold_action:
  action: none
double_tap_action:
  action: none
```

Un exemple de dashboard plus complet est fourni dans
[`examples/dashboard_batiment.yaml`](examples/dashboard_batiment.yaml).

## Confidentialité

Les adresses e-mail, images de profil et URL de médias ne sont pas exposées dans
les attributs des entités. Home Assistant peut cependant enregistrer les noms des
membres et les métadonnées des messages dans son historique. Un exemple
d'exclusion est fourni dans
[`examples/recorder_exclusions.yaml`](examples/recorder_exclusions.yaml).

## Dépannage

- Redémarrer Home Assistant après l'installation ou une mise à jour.
- Vérifier l'accès HTTPS à `api.hapiix.io` depuis Home Assistant.
- Utiliser le code reçu le plus récemment en cas d'échec d'authentification.
- Consulter **Paramètres → Système → Journaux** en filtrant sur `hapiix`.
- Ne jamais désactiver la vérification des certificats TLS.

## Projet non officiel

Ce projet est indépendant et n'est ni développé, ni approuvé, ni maintenu par
Hapiix. Il dépend d'une API susceptible d'évoluer. Les noms Hapiix et Home
Assistant appartiennent à leurs propriétaires respectifs.

## Licence

Le code est distribué sous licence [MIT](LICENSE).

