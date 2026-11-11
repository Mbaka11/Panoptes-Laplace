# Textes destinés aux participants (français)

> **STATUT : PROVISOIRE.** Ébauche de travail rédigée en français canadien (vouvoiement). Ce n'est ni un avis juridique, ni une déclaration de conformité, ni un formulaire de consentement approuvé. Elle doit être révisée par une personne qualifiée avant tout usage avec un participant externe (voir la section 8 et D-041). Le propriétaire du projet peut s'en servir comme texte de travail pour sa propre collecte.
>
> Elle ne promet que ce que les documents du projet décident. Ce qui n'est pas décidé est marqué `[À DÉCIDER : ...]`. Les clés Info.plist restent **[NON VÉRIFIÉ]** tant qu'elles n'ont pas été comparées au SDK installé (voir [sensor-probe-spec.md](sensor-probe-spec.md)). Aucun algorithme de chiffrement n'est annoncé : la conception du transfert est provisoire ([transfer-package-design.md](transfer-package-design.md)).

Documents sources : [trust-and-data-governance.md](trust-and-data-governance.md), [sensor-probe-spec.md](sensor-probe-spec.md), [collection-probe.md](collection-probe.md), [owner-manual-procedures.md](owner-manual-procedures.md), [transfer-package-design.md](transfer-package-design.md), [decisions.md](decisions.md).

---

## 1. Écran d'introduction

**Panoptes Laplace** (noms de travail) est un projet de recherche ouvert et fondé sur le consentement. Il vise à vous aider à explorer, dans le temps, ce que vos propres traces numériques peuvent révéler de votre vie, à partir d'exports historiques et de données de votre iPhone que vous autorisez. Dans la première version, **c'est vous qui utilisez l'outil sur vos propres données**, sur un poste Mac local. Un chercheur n'entre en jeu que si vous l'autorisez expressément (section 5).

**Ce que Panoptes Laplace n'est pas :**

- Aucune collecte cachée : rien n'est collecté sans que vous l'ayez compris et accepté, source par source.
- Aucune vente de vos données et aucun profil publicitaire.
- Aucun diagnostic, aucun avis médical ni financier. Les données de santé sont présentées comme des mesures ou des associations personnelles, pas comme une analyse médicale.
- Un texte produit par un modèle de langage n'est pas une preuve. Les conclusions reposent sur des méthodes statistiques; un modèle peut proposer des hypothèses ou expliquer, rien de plus.
- Aucune synchronisation continue dans la version 1 : les données quittent votre téléphone seulement quand vous lancez un export.
- Aucun outil externe d'intelligence artificielle ne reçoit vos données tant qu'une décision et une autorisation distinctes n'existent pas.

Vous pouvez dire non à n'importe quelle source, faire une pause, retirer votre consentement ou supprimer vos données à tout moment, sans pénalité.

`[Continuer]` `[Plus tard]`

---

## 2. Cartes d'information et de consentement par source

Règles communes :

- Chaque source a sa propre carte et sa propre réponse **Oui / Non**. Aucun consentement groupé. Répondre Non à une source ne change rien aux autres.
- La carte s'affiche **avant** la demande d'autorisation d'iOS. « Pas maintenant » laisse la source désactivée et ne déclenche aucune demande système.
- L'autorisation d'iOS est nécessaire mais n'est pas suffisante : elle ne remplace pas cette explication.
- Dans la phase actuelle (laboratoire de faisabilité de collecte), les données restent sur le téléphone jusqu'à un export lancé par vous. Les valeurs de conservation sont à fixer (section 8).

### 2.1 Localisation (Core Location)

| Rubrique | Texte |
|---|---|
| Ce qui est collecté | La position que votre iPhone rapporte, à la fréquence affichée à l'écran suivant, ainsi que l'heure de chaque relevé. Le niveau de précision accordé par iOS (précis ou approximatif) est noté tel quel. |
| Ce qui ne l'est pas | Les noms de lieux, vos contacts, la position d'autres personnes. Aucune conclusion n'est tirée d'une absence de relevé. |
| Mode d'utilisation | D'abord seulement quand l'application est ouverte. Un second choix, **facultatif**, permet de continuer écran verrouillé ou application hors de l'écran, afin de mesurer l'exhaustivité du relevé et la consommation de batterie. Un indicateur système peut alors s'afficher. Le test en premier plan seul reste utile. |
| Batterie | Le relevé en arrière-plan peut augmenter la consommation de batterie; le test sert justement à la mesurer. Si l'application est fermée de force, des relevés peuvent manquer : ces trous sont notés comme des trous, pas comme de l'immobilité. |
| Où c'est stocké | Sur ce téléphone seulement, jusqu'à ce que vous lanciez un export. `[À DÉCIDER : méthode de stockage protégé sur l'iPhone]` |
| Combien de temps | `[À DÉCIDER : durée de conservation sur le téléphone]` |
| Comment arrêter | Bouton Pause dans l'application (la période en pause est notée comme une pause volontaire), ou désactivation dans Réglages > Confidentialité et sécurité > Service de localisation. Rétrograder « toujours » vers « pendant l'utilisation » est noté comme un changement de portée. |
| Effet de la suppression | Les relevés de position sur le téléphone sont effacés. Les exports déjà créés ou partagés ne sont pas rappelés automatiquement (section 4). Les constats dérivés qui en dépendent sont retirés ou invalidés (section 4). |

**Vos choix :** `[Oui, localisation en premier plan]` `[Oui, aussi en arrière-plan (facultatif)]` `[Non]`

### 2.2 Mouvement (Core Motion)

| Rubrique | Texte |
|---|---|
| Ce qui est collecté | Les types de mouvement que l'iPhone a déjà détectés (marche, immobile, en véhicule, etc.) et le nombre de pas. Trois fonctions séparées peuvent être testées : historique borné, mises à jour en direct et podomètre. Leur disponibilité et la profondeur de leur historique peuvent différer. |
| Ce qui ne l'est pas | Les données brutes de l'accéléromètre et votre position. |
| Si l'historique est absent | L'écran l'indique au lieu d'afficher zéro. |
| Où c'est stocké | Sur ce téléphone seulement, jusqu'à un export lancé par vous. `[À DÉCIDER : méthode de stockage protégé]` |
| Combien de temps | `[À DÉCIDER : durée de conservation]` |
| Comment arrêter | Pause dans l'application (arrête les mises à jour en direct et les requêtes d'historique) ou désactivation dans les Réglages d'iOS. À la reprise, vous choisissez si la période en pause est récupérée. |
| Effet de la suppression | Les enregistrements de mouvement sur le téléphone sont effacés; mêmes limites et même cascade que pour toute source (section 4). L'historique conservé par iOS lui-même n'est pas supprimé par l'application. |

**Vos choix :** `[Oui]` `[Non]`

### 2.3 Santé (HealthKit)

| Rubrique | Texte |
|---|---|
| Ce qui est collecté | Les types de données Santé que **vous choisissez** dans une liste à l'écran (candidats : pas, distance de marche ou de course; fréquence cardiaque et sommeil seulement si un appareil ou une application en a réellement produit). Pour chaque type : le nombre d'enregistrements, les dates de début et de fin, l'unité, et la catégorie de producteur (cet iPhone, une autre application, un appareil externe, saisie manuelle, inconnu) sans les noms. |
| Ce qui ne l'est pas | L'application **lit seulement** : elle n'écrit rien dans Santé. Aucun type que vous n'avez pas choisi. Il ne s'agit pas d'une analyse médicale. |
| Point important | iOS **ne dit pas** à l'application si l'accès en lecture a été refusé pour un type. Un résultat vide peut donc vouloir dire : aucune donnée, aucune permission ou aucune activité enregistrée. L'écran affichera alors **« inconnu »** et jamais « 0 » ni « refusé ». Des enregistrements présents prouvent seulement que la lecture fonctionne pour ce type et cette période. |
| Chevauchements | Plusieurs producteurs peuvent enregistrer la même chose (par exemple téléphone et montre). L'application ne les fusionne ni ne les additionne. Les valeurs calculées sur un intervalle restent des agrégats, distincts des échantillons individuels. |
| Où c'est stocké | Sur ce téléphone seulement, jusqu'à un export lancé par vous. `[À DÉCIDER : méthode de stockage protégé]` |
| Combien de temps | `[À DÉCIDER : durée de conservation]` |
| Comment arrêter | Pause dans l'application, ou modification de l'accès dans Santé (profil > Confidentialité > Apps) ou dans les Réglages. La révocation de l'accès n'est pas directement observable par l'application. |
| Effet de la suppression | Les copies de données Santé stockées par Panoptes sont effacées. Vos données dans l'app Santé d'Apple ne sont pas touchées. Mêmes limites que pour toute source (section 4). |

**Vos choix, par type de donnée :** `[Oui]` `[Non]` pour chacun.

### 2.4 Calendrier et Rappels (EventKit)

| Rubrique | Texte |
|---|---|
| Ce qui est collecté | Les heures des événements du calendrier et, séparément et facultativement, les échéances des rappels. Un événement planifié montre ce qui était prévu, pas ce que vous avez réellement fait. |
| Ce qui ne l'est pas | Les noms des participants, les contacts, les descriptions et les liens de réunion ne sont pas enregistrés. Les titres libres sont désactivés par défaut parce qu'ils nomment souvent d'autres personnes. `[À DÉCIDER : traitement du titre : empreinte, étiquette choisie par vous, ou exclusion]` |
| Particularité d'iOS | L'autorisation demandée par iOS peut être plus large que ce que l'application utilise; la portée exacte est nommée en langage clair à l'écran. |
| Données de test | Par défaut, le test utilise une entrée synthétique que vous créez vous-même. La lecture de votre vrai calendrier n'est permise qu'une fois les protections de données réelles en place. |
| Où c'est stocké | Sur ce téléphone seulement, jusqu'à un export lancé par vous. `[À DÉCIDER : méthode de stockage protégé]` |
| Combien de temps | `[À DÉCIDER : durée de conservation]` |
| Comment arrêter | Pause dans l'application ou modification de l'accès dans les Réglages. Les événements de la période en pause restent dans votre calendrier et peuvent être lus plus tard si vous le décidez. |
| Effet de la suppression | Les copies stockées par Panoptes sont effacées; votre calendrier et vos rappels ne sont pas modifiés. Mêmes limites que pour toute source (section 4). |

**Vos choix :** `[Oui, calendrier]` `[Oui, rappels]` `[Non]` (chacun séparément).

### 2.5 Rapport de confidentialité des apps (App Privacy Report)

| Rubrique | Texte |
|---|---|
| Ce qui est collecté | Vous exportez vous-même le rapport depuis Réglages > Confidentialité et sécurité > Rapport de confidentialité des apps (si vous l'avez activé; le laisser désactivé est un choix valide). Panoptes lit le fichier que **vous** lui fournissez. |
| Ce qui n'est pas couvert | Il n'existe aucun historique avant l'activation, et le rapport partageable couvre au plus environ sept jours. L'activité de navigation privée est exclue : l'absence d'une entrée ne prouve pas l'absence d'activité. Un accès à un domaine ne prouve ni un contenu transmis, ni un profil détenu par une entreprise, ni une cause. |
| Où c'est stocké | Le fichier reçu est en clair; il passe par une zone d'attente à durée de vie déclarée, puis est supprimé ou rechiffré après lecture. Gardez au plus une copie, hors de tout dossier synchronisé que vous ne contrôlez pas, et notez où elle se trouve. `[À DÉCIDER : durée de la zone d'attente et emplacement]` |
| Combien de temps | `[À DÉCIDER : durée de conservation]` |
| Comment arrêter | Ne pas exporter, ou désactiver le rapport dans les Réglages. |
| Effet de la suppression | Les enregistrements importés et les éléments dérivés sont retirés ou invalidés. Le fichier d'origine dans vos Fichiers ou téléchargements reste à supprimer par vous; il est listé comme copie à vérifier. |

**Votre choix :** `[Oui, j'importerai un rapport]` `[Non]`

### 2.6 Export de compte (initié par vous)

| Rubrique | Texte |
|---|---|
| Ce qui est collecté | Vous demandez vous-même à **un** service que vous utilisez réellement de vous fournir son export (le service sera nommé ici : `[À DÉCIDER : service retenu; Google Takeout est un candidat, pas un choix]`). Panoptes examine quels champs existent : contenu consulté, recherches, interactions, horodatages, durées, ou aucun champ pertinent. |
| Ce qui reste hors de la collecte | Vos identifiants et mots de passe ne sont jamais demandés. Les contenus de tiers non essentiels (messages, visages, champs de contacts) sont exclus. Aucune durée de visionnement et aucune profondeur de défilement ne sont déduites de l'écart entre deux événements. Un export ne montre pas ce que l'entreprise sait de vous. |
| Où c'est stocké | Même régime que le rapport de confidentialité : fichier reçu en clair, zone d'attente à durée de vie déclarée, suppression ou rechiffrement après lecture. `[À DÉCIDER : durée et emplacement]` |
| Combien de temps | `[À DÉCIDER : durée de conservation]` |
| Comment arrêter | Ne pas demander l'export ou ne pas le fournir. |
| Effet de la suppression | Les enregistrements importés et les éléments dérivés sont retirés ou invalidés; l'export original chez vous et chez le fournisseur n'est pas supprimé par Panoptes. |

**Votre choix :** `[Oui, pour ce service]` `[Non]`

### 2.7 Temps d'écran (volet expérimental, autorisation séparée)

| Rubrique | Texte |
|---|---|
| De quoi il s'agit | Un test distinct pour savoir si Apple permet à une application installée sur ce téléphone d'afficher, ou d'exporter, votre usage des apps et des sites. **Il peut être impossible** selon votre compte, votre région ou l'équipement d'accès; un échec est un résultat utile. |
| Ce qui est collecté | Si le test fonctionne en affichage standard, le rapport s'affiche dans l'application mais ne peut pas en être copié. Un export officiel distinct pourrait n'exister que pour certaines régions et conditions; un succès en développement ne prouve pas qu'il soit offert à d'autres utilisateurs. |
| Ce qui ne l'est pas | Ce test ne bloque aucune application et ne modifie aucune limite. Aucun contenu consulté n'est capté. |
| Particularité d'iOS | iOS peut décrire la demande comme la gestion de Temps d'écran et la présente séparément des autres demandes. |
| Où c'est stocké | Rien n'est exporté tant qu'un enregistrement réel n'a pas été retourné; le cas échéant, mêmes règles que les autres sources. `[À DÉCIDER : stockage, si des enregistrements sont retournés]` |
| Combien de temps | `[À DÉCIDER : durée de conservation]` |
| Comment arrêter | Retirer l'accès dans les Réglages d'iOS. |
| Effet de la suppression | Le cas échéant, mêmes règles que les autres sources. |

**Votre choix :** `[Oui, essayer]` `[Non]`

---

## 3. Vue d'ensemble : ce que vous gardez toujours en main

À tout moment, depuis l'écran « Données et copies » :

- voir l'état de chaque source (activée, en pause, désactivée, bloquée par iOS, inconnue) et les trous de collecte;
- mettre une source en pause ou la reprendre;
- créer un export, en choisissant les sources et les dates, et voir ce qu'il contiendra avant de le créer;
- voir la liste des copies que l'application a créées et supprimer celles qu'elle contrôle;
- tout supprimer du téléphone.

Dans la phase de test actuelle, un export de données réelles reste bloqué tant que le stockage protégé, le transfert chiffré, la gestion des clés et la suppression des copies de test ne sont pas en place. Un export de test non protégé est étiqueté `UNPROTECTED_TEST_ARTIFACT` et ne contient que des données synthétiques ou jetables.

---

## 4. Pause, export, correction, suppression, retrait

### Pause
Vous pouvez suspendre une source ou toute la collecte. Une période en pause est notée comme un trou, jamais comme une absence d'activité. À la reprise, vous décidez si la période manquée est récupérée lorsque c'est possible.

### Export
- Il est toujours lancé par vous, par lots, et jamais en continu dans la version 1.
- Vous choisissez les sources et la période. Les données voyagent dans un paquet chiffré vers votre poste Mac local (ou, si vous l'autorisez, celui d'un chercheur). `[À DÉCIDER : format du paquet, algorithme et échange de clés; la conception est provisoire]`
- « La feuille de partage s'est affichée » ne veut pas dire « l'export a réussi ».

### Correction
Vous pouvez inspecter, corriger ou rejeter toute interprétation. Votre correction est enregistrée comme un événement distinct; elle ne réécrit pas silencieusement l'historique des résultats du modèle. Votre accord avec un constat n'en fait pas une preuve statistique.

### Suppression
Vous pouvez demander la suppression de vos données sur chaque copie que le projet contrôle : le téléphone, les paquets d'export générés, les enregistrements bruts importés sur le Mac, les événements normalisés et objets de l'ontologie, les caractéristiques et caches de modèles, les prédictions et paquets de résultats publiés.

**Cascade :** lorsqu'un enregistrement source est supprimé, les constats et éléments dérivés qui en dépendent sont retirés ou marqués invalides. Les journaux de correction ne conservent pas les valeurs sensibles. `[À DÉCIDER : règles exactes de cascade; la sémantique de suppression doit être conçue et vérifiée avant toute participation externe]`

**Limites, énoncées sans détour :**

- Une copie déjà déchiffrée par un destinataire (vous-même sur une autre machine, ou un chercheur autorisé) ne peut pas être « rappelée » techniquement. Nous suivons les demandes de suppression et leur confirmation, sans promettre l'effacement universel.
- Les sauvegardes (iCloud, ordinateur, Time Machine) et les copies faites par d'autres applications ou destinations ne sont pas contrôlées par Panoptes. Elles sont listées comme **non vérifiées**, pas comme supprimées. `[À DÉCIDER : traitement des sauvegardes, si elles sont introduites]`
- Les exports originaux chez un fournisseur de service ou dans vos dossiers restent sous votre responsabilité.
- Les copies de test de données réelles font l'objet d'un inventaire avec un responsable, un emplacement, une date de création et une suppression vérifiée.

### Retrait du consentement
Vous pouvez retirer votre consentement, en tout ou en partie, **à tout moment et sans pénalité**. Le retrait arrête la collecte future et tout partage futur; il déclenche les suppressions décrites ci-dessus, avec les limites indiquées.

---

## 5. Mode assisté par un chercheur (facultatif)

Ce mode n'existe que si vous l'autorisez **expressément**. Installer l'application ou utiliser l'outil seul n'est pas un consentement à communiquer des données à un chercheur.

Avant d'autoriser, vous devez savoir, par écrit :

- **qui** est le chercheur et **quel but** précis est visé : `[À DÉCIDER : identité, rôle, objet de l'étude]`;
- **ce que le chercheur reçoit** : uniquement le contenu du paquet que vous avez choisi (sources, dates), identifiable dans la version 1;
- **ce que le chercheur ne peut pas voir** : tout ce que vous n'avez pas inclus dans le paquet; il n'a aucun accès continu à votre téléphone ni à une base de données infonuagique, car il n'y en a pas dans la version 1;
- **l'isolement** : votre espace de travail est distinct de ceux des autres participants; vos enregistrements ne sont pas fusionnés avec ceux d'autrui et aucune analyse croisée entre participants n'est faite. `[À DÉCIDER : mécanismes techniques d'isolement; un identifiant d'espace de travail seul n'est pas une frontière de sécurité]`;
- **le transfert** : par lot, chiffré, lancé par vous. Vous pouvez révoquer l'accès futur; cela n'efface pas une copie déjà déchiffrée par le destinataire (section 4);
- **la durée de conservation chez le chercheur et la preuve de suppression** : `[À DÉCIDER]`;
- qu'**aucun fournisseur externe d'IA** ne reçoit vos données sans décision et autorisation distinctes.

Le chercheur ne construit pas de dossier sur des tiers et n'agit pas à votre place. Les résultats qui comptent sont revus par une personne dont le rôle est visible.

**Votre choix :** `[Oui, j'autorise ce chercheur pour ce but]` `[Non]`

---

## 6. Constats et incertitude

- **Une corrélation n'est pas une causalité.** Un lien observé entre deux choses est présenté comme une association.
- **« Inconnu » n'est pas zéro.** Une donnée manquante, non vérifiée ou non lisible n'est jamais traitée comme la preuve qu'un événement n'a pas eu lieu.
- **Un résultat nul ou non concluant est valide.** Aucun résultat positif n'est obligatoire.
- **Chaque constat est traçable** : sources, méthode et version, éléments de preuve, niveau de confiance, et vos corrections.
- **Observation, événement normalisé, hypothèse, inférence et prédiction sont des choses distinctes.** Une prose générée par un modèle n'est jamais une observation.
- **Rien n'est automatique.** Aucune action importante, notification ou intervention n'est lancée sans votre approbation; ces fonctions sont facultatives.
- **Santé :** les mesures sont des associations personnelles, pas des diagnostics.
- Une courte période de collecte vérifie le fonctionnement du système; elle ne suffit pas pour établir une signification statistique.

Vous pouvez corriger ou rejeter tout constat. Une correction n'est pas une preuve, et elle est conservée comme telle.

---

## 7. Textes d'autorisation iOS (clés Info.plist)

Ces textes s'affichent dans la fenêtre système d'iOS. Ils correspondent aux textes anglais de [sensor-probe-spec.md](sensor-probe-spec.md) et ne promettent rien de plus que la sonde ne fait. **Toutes les clés sont [NON VÉRIFIÉES]** : à confirmer avec le SDK installé et sur l'appareil avant usage. Le français s'applique via la localisation (`InfoPlist.strings`); la structure de localisation est `[À DÉCIDER]` et dépend de l'étape ENV-01.

| Clé Info.plist | Texte français | Texte anglais |
|---|---|---|
| `NSLocationWhenInUseUsageDescription` [NON VÉRIFIÉ] | « La sonde Panoptes enregistre la position de ce téléphone lorsque l'application est ouverte, pour évaluer la qualité de la collecte de position. Les données restent sur ce téléphone jusqu'à ce que vous les exportiez. » | "Panoptes Sensor Probe records this phone's location while the app is open so you can see how well location collection works. Data stays on this phone until you export it." |
| `NSLocationAlwaysAndWhenInUseUsageDescription` [NON VÉRIFIÉ; le nom peut varier selon le SDK] | « Permet au test de continuer à enregistrer la position lorsque l'écran est verrouillé, afin de mesurer l'exhaustivité et la consommation de batterie. Vous pouvez le mettre en pause ou l'arrêter à tout moment. » | "Allows the test to keep recording location when the screen is locked, so the probe can measure completeness and battery use. You can pause or stop it at any time." |
| `NSMotionUsageDescription` [NON VÉRIFIÉ] | « La sonde Panoptes lit les types de mouvement détectés par le téléphone et le nombre de pas, pour vérifier quelles données de mouvement peuvent être collectées. Les données restent sur ce téléphone jusqu'à ce que vous les exportiez. » | "Panoptes Sensor Probe reads the phone's motion and activity classifications and step counts to test what movement information can be collected. Data stays on this phone until you export it." |
| `NSHealthShareUsageDescription` [NON VÉRIFIÉ] | « La sonde Panoptes lit les types de données Santé que vous choisissez, pour vérifier quelles données de santé et d'activité peuvent être collectées. Rien n'est écrit dans Santé, et les données restent sur ce téléphone jusqu'à ce que vous les exportiez. » | "Panoptes Sensor Probe reads the Health data types you choose to test what health and activity information can be collected. Nothing is written to Health, and data stays on this phone until you export it." |
| `NSCalendarsFullAccessUsageDescription` [NON VÉRIFIÉ; les SDK plus anciens utilisaient `NSCalendarsUsageDescription`] | « La sonde Panoptes lit les heures des événements de votre calendrier, pour vérifier comment le contexte planifié peut être collecté. Elle n'enregistre ni les participants, ni les notes, ni les liens, et les données restent sur ce téléphone jusqu'à ce que vous les exportiez. » | "Panoptes Sensor Probe reads event times from your calendar to test how scheduled context can be collected. It does not save attendees, notes, or links, and data stays on this phone until you export it." |
| `NSRemindersFullAccessUsageDescription` [NON VÉRIFIÉ; les SDK plus anciens utilisaient `NSRemindersUsageDescription`] | « La sonde Panoptes lit les échéances de vos rappels, pour vérifier comment le contexte planifié peut être collecté. Les données restent sur ce téléphone jusqu'à ce que vous les exportiez. » | "Panoptes Sensor Probe reads reminder due dates to test how scheduled context can be collected. Data stays on this phone until you export it." |

Non utilisées : `NSHealthUpdateUsageDescription` (aucun accès en écriture n'est demandé; si le SDK l'exige, le consigner comme constat, sans ajouter d'écriture). Aucun texte d'autorisation n'est présumé pour Temps d'écran (Family Controls) : si le SDK en exige un, le consigner comme constat. La déclaration d'arrière-plan pour la position n'est pas un texte; elle n'est ajoutée que si le test d'arrière-plan est construit.

---

## 8. À vérifier avant usage réel

Rien ici n'est un avis juridique ni une affirmation de conformité. Ce sont des points à faire examiner par une personne qualifiée.

- [ ] **Examen juridique et éthique** par une personne qualifiée, avant tout participant externe. `[À DÉCIDER : qui, quand]`
- [ ] **Lois sur la protection des renseignements personnels** : déterminer, avec une personne qualifiée, si et comment la *Loi sur la protection des renseignements personnels dans le secteur privé* du Québec (telle que modifiée par la Loi 25) et la LPRPDE (PIPEDA) s'appliquent à ce projet, y compris pour la collecte de renseignements sensibles (santé, localisation), les exigences de consentement, la conservation et la destruction, la communication à un chercheur et un éventuel traitement hors du Québec ou du Canada. **À vérifier : aucune affirmation de conformité n'est faite.**
- [ ] **Éthique de la recherche** : déterminer si une évaluation éthique est requise selon le contexte du projet. `[À DÉCIDER]`
- [ ] **Âge : adultes seulement.** Seules les personnes adultes peuvent participer. `[À DÉCIDER : âge légal applicable au lieu de résidence et méthode de confirmation]`
- [ ] **Personne-ressource** pour les questions, les retraits et les demandes de suppression : `[À DÉCIDER : nom, courriel ou autre moyen de contact, délai de réponse]`.
- [ ] **Valeurs de conservation à fixer** : téléphone; zone d'attente des fichiers importés; paquets d'export; poste Mac de travail; copies chez un chercheur; sauvegardes. `[À DÉCIDER : chaque valeur]`
- [ ] **Stockage et transfert protégés** : méthode de stockage sur l'iPhone, format du paquet, algorithmes, échange et rotation des clés, suppression des copies de test (conception provisoire).
- [ ] **Isolement des espaces de travail** : conception et tests avec espaces synthétiques avant tout travail avec un participant externe.
- [ ] **Fournisseur d'IA externe** : aucune donnée n'est transmise tant qu'une décision distincte ne définit ce qui est transmis, la conservation, le lieu de traitement et la suppression.
- [ ] **Relecture en langage clair** de ces textes avec des personnes non expertes; relecture linguistique (registre québécois et canadien, vouvoiement), y compris la version anglaise.
- [ ] **Vérification des clés Info.plist** auprès du SDK installé, après l'étape ENV-01 (la sortie complète de `xcodebuild -version` est encore en attente).
- [ ] **Traitement du titre des événements** (hachage, étiquette ou exclusion) et service d'export de compte retenu.
- [ ] **Appartenance et droits Apple** : la disponibilité de Temps d'écran en développement au Canada ne prouve pas son admissibilité pour d'autres utilisateurs; à vérifier séparément.
- [ ] **Politique de sécurité** du dépôt avant d'accepter des signalements externes.
