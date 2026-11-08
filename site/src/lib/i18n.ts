export type Lang = "fr" | "en";
export type PageId = "home" | "results" | "answers" | "method";

export const REPO_URL = "https://github.com/hasdaouiryma16-cmd/kabyle-llm-benchmark";
export const PROFILE_URL = "https://github.com/hasdaouiryma16-cmd";

/** Chemins relatifs à la base du site, par page et par langue. */
export const ROUTES: Record<PageId, Record<Lang, string>> = {
  home: { fr: "", en: "en/" },
  results: { fr: "resultats/", en: "en/results/" },
  answers: { fr: "reponses/", en: "en/answers/" },
  method: { fr: "methode/", en: "en/method/" },
};

const fr = {
  siteName: "Kabyle LLM Benchmark",
  nav: { home: "Accueil", results: "Résultats", answers: "Réponses", method: "Méthode" } as Record<PageId, string>,
  pageTitle: {
    home: "Les IA parlent-elles kabyle ?",
    results: "Résultats",
    answers: "Comparer les réponses",
    method: "Méthode",
  } as Record<PageId, string>,
  description:
    "Un benchmark ouvert de la maîtrise du kabyle (taqbaylit) par les modèles de langage, noté à l'aveugle par une locutrice native, et la mesure de ce que few-shot, RAG et fine-tuning leur apportent.",
  switchLang: "English",
  theme: "Changer de thème",
  menu: "Menu",
  locale: "fr-FR",

  // ── Accueil ──
  greeting: "Azul !",
  heroTitle: "Les IA parlent‑elles kabyle ?",
  heroLead:
    "15 configurations de modèles de langage, 41 tests écrits par une locutrice native, 615 réponses notées à l'aveugle. Ce que les modèles savent vraiment du kabyle, et ce qu'on peut leur apprendre.",
  heroCta: "Voir les résultats",
  heroCta2: "Lire les réponses",
  kpi: {
    best: "meilleur score, sans aucune aide",
    gain: "plus forte progression, par fine-tuning",
    graded: "réponses notées à la main, à l'aveugle",
    tests: "tests, en 6 catégories",
  },
  findingsTitle: "Ce qu'il faut retenir",
  findings: (v: FindingValues) => [
    {
      h: "Un seul modèle sait déjà le kabyle",
      p: `${v.bestLabel} atteint ${v.bestPct} % sans aucune aide. Aucun autre modèle n'en approche, même avec les meilleures aides.`,
    },
    {
      h: "Pour les grands modèles, 5 exemples suffisent",
      p: `Montrer quelques phrases traduites dans la consigne (few-shot) fait gagner ${v.fewshotLarge} points à ${v.fewshotLargeLabels}. C'est l'aide la plus simple et la plus efficace pour eux.`,
    },
    {
      h: "Les petits modèles partent de zéro",
      p: `${v.smallLabels} obtiennent ${v.smallBase} : ils répondent dans une autre langue, ou inventent des mots qui ressemblent à du kabyle.`,
    },
    {
      h: "Le fine-tuning transforme un petit modèle",
      p: `Entraîné sur des paires kabyle–français, ${v.ftLabel} passe de ${v.ftBefore} % à ${v.ftAfter} %. Il dépasse alors des modèles bien plus grands utilisés sans aide : ${v.ftBeats}.`,
    },
    {
      h: "La conversation reste le point faible",
      p: "Traduire est à la portée des meilleurs modèles. Tenir une conversation naturelle en kabyle ne l'est pour aucun : c'est la catégorie la plus basse partout.",
    },
  ],
  homeTopTitle: "Le podium",
  homeTopMore: "Classement complet",
  whyTitle: "Pourquoi le kabyle ?",
  whyBody: [
    "Le kabyle (taqbaylit) est une langue berbère parlée par plusieurs millions de personnes en Kabylie, dans le nord de l'Algérie, et par une importante diaspora, notamment en France. Il s'écrit surtout en alphabet latin, avec des lettres propres comme ɛ, ɣ, ḥ ou ṭ, et aussi en tifinagh (ⵜⵉⴼⵉⵏⴰⵖ).",
    "C'est une langue peu dotée : peu de textes numériques, peu d'outils, une orthographe qui varie. Les modèles de langage, entraînés surtout sur l'anglais, la confondent souvent avec l'arabe, le français ou d'autres langues berbères.",
  ],
  facts: [
    { value: "≈ 7 200", label: "articles sur Wikipédia en kabyle" },
    { value: "≈ 94 000", label: "paires de phrases kabyle–français sur Tatoeba" },
  ],

  // ── Résultats ──
  resultsLead:
    "Toutes les notes sont données à la main, de 0 à 3, sans savoir quel modèle a répondu, puis ramenées en pourcentage. Les fourchettes indiquent la marge d'incertitude à 95 %.",
  filterAll: "Tout",
  filterBase: "Modèles seuls",
  filterHelped: "Avec une aide",
  rankingTitle: "Classement général",
  colModel: "Modèle",
  colMethod: "Aide",
  colScore: "Score",
  colRange: "Score et fourchette à 95 %",
  colChrf: "chrF++",
  colN: "Réponses",
  matrixTitle: "Ce que chaque aide apporte",
  matrixLead:
    "Chaque ligne est un modèle, chaque colonne une façon de l'aider. Le gain est mesuré test par test par rapport au modèle seul.",
  matrixNotTested: "non testé",
  matrixNotApplicable: "impossible",
  matrixNaNote: "Le fine-tuning n'est possible que sur les modèles dont les poids sont publics : Gemini et Mistral Large 4 ne le permettent pas.",
  gainsChartTitle: "Du modèle seul au modèle aidé",
  gainsChartLead: "Le point gris est le modèle seul ; chaque marque colorée, le même modèle avec une aide.",
  categoriesTitle: "Par catégorie",
  categoriesLead:
    "Peu de tests par catégorie (voir le nombre sous chaque titre) : ces scores donnent une tendance, pas un classement.",
  testsCount: (n: number) => `${n} test${n > 1 ? "s" : ""}`,
  agreementTitle: "La note automatique confirme-t-elle la note humaine ?",
  agreementBody: (rho: string, n: number) =>
    `Corrélation de rang de Spearman de ${rho} entre la note humaine et chrF++ sur ${n} réponses : un accord fort. La métrique automatique classe les réponses dans le même sens que la locutrice, mais ne la remplace pas : elle ne comprend pas le sens.`,
  metaLine: (version: string, hash: string, date: string) => `Jeu de test ${version} · empreinte SHA-256 ${hash}… · résultats exportés le ${date}`,

  // ── Réponses ──
  answersLead:
    "Choisissez un test pour lire les réponses des 15 configurations, avec la note qu'elles ont reçue. Les références sont celles de l'autrice ; les réponses des modèles sont publiées telles quelles.",
  pickCategory: "Catégorie",
  allCategories: "Toutes",
  pickTest: "Test",
  search: "Rechercher dans les consignes…",
  sortBy: "Trier par",
  sortScore: "note",
  sortModel: "modèle",
  context: "Texte",
  prompt: "Consigne",
  source: "Texte à traduire",
  references: "Référence de l'autrice",
  answer: "Réponse",
  noAnswer: "Aucune réponse",
  score: "Note",
  showMore: "Afficher tout",
  showLess: "Réduire",
  scoreScale: ["Faux ou autre langue", "Partiellement correct", "Correct, erreurs mineures", "Correct et naturel"],

  // ── Méthode ──
  methodLead: "Comment le benchmark a été construit, ce que veulent dire les chiffres, et ce qu'ils ne disent pas.",
  testsetTitle: "Le jeu de test",
  testsetBody: (pub: number, priv: number) => [
    `Tous les textes kabyles du jeu de test (références, textes de compréhension, consignes en kabyle) sont écrits à la main par une locutrice native. Aucun n'est généré par une IA.`,
    `Le jeu compte ${pub + priv} tests : ${pub} publics, utilisés pour ces résultats, et ${priv} gardés privés pour de futures évaluations à l'abri de toute fuite dans les données d'entraînement.`,
  ],
  categoryDescriptions: {
    translation_fr_kab: "Traduire une phrase du français vers le kabyle.",
    translation_kab_fr: "Traduire une phrase du kabyle vers le français.",
    comprehension: "Lire un court texte kabyle et répondre à une question dessus.",
    culture: "Répondre à une question sur la culture et les traditions kabyles.",
    writing: "Écrire en kabyle, en alphabet latin ou en tifinagh.",
    conversation: "Répondre naturellement à une réplique, comme dans une discussion.",
  } as Record<string, string>,
  protocolTitle: "Le protocole",
  protocol: [
    { h: "Même consigne pour tous", p: "Chaque modèle reçoit exactement la même consigne, sans message système, avec une température de 0. Chaque réponse est enregistrée avec ses paramètres exacts." },
    { h: "Notation à l'aveugle", p: "Les réponses sont tirées au hasard, tous modèles confondus. L'autrice note sans savoir quel modèle a répondu ; le modèle n'est révélé qu'après la note." },
    { h: "Aucune fuite", p: "Les exemples, l'index RAG et les données d'entraînement sont vérifiés automatiquement : aucune phrase du jeu de test n'y figure." },
  ],
  scaleTitle: "L'échelle de notation",
  methodsTitle: "Les trois aides testées",
  methods: [
    { id: "fewshot", h: "Few-shot", p: "On ajoute à la consigne 5 paires de phrases kabyle–français, choisies parmi les plus proches de la question dans le corpus Tatoeba." },
    { id: "rag", h: "RAG (recherche augmentée)", p: "Au moment de répondre, le modèle reçoit les 8 passages les plus proches de la question, trouvés par recherche sémantique (bge-m3) dans un corpus kabyle–français." },
    { id: "finetuned", h: "Fine-tuning (QLoRA)", p: "On ré-entraîne légèrement le modèle sur des dizaines de milliers de paires kabyle–français, sur un GPU gratuit. Possible seulement pour les modèles aux poids publics." },
  ],
  glossaryTitle: "Glossaire",
  glossary: [
    { t: "Score humain", d: "Note moyenne donnée à la main (0 à 3), ramenée sur 100 : 2,4 / 3 donne 80 %. C'est la mesure principale." },
    { t: "Fourchette à 95 %", d: "Avec 41 tests, un score est approximatif. La fourchette donne la zone où se trouve très probablement le vrai niveau du modèle (bootstrap). Si deux fourchettes se chevauchent largement, l'écart n'est pas significatif." },
    { t: "Gain (en points)", d: "Différence entre le score du modèle aidé et celui du modèle seul, mesurée sur les mêmes tests. +38 points : de 37 % à 75 %." },
    { t: "chrF++", d: "Note automatique (0 à 100) qui compare la réponse à la référence lettre par lettre et mot par mot. Utile pour confirmer, mais elle ne comprend pas le sens : une bonne traduction formulée autrement est pénalisée." },
    { t: "Modèle seul (base)", d: "Le modèle tel quel, avec la simple consigne." },
    { t: "Poids ouverts", d: "Modèle téléchargeable, qu'on peut faire tourner sur sa propre machine et ré-entraîner. Ici : Qwen3.5 4B et Ministral 3 8B." },
  ],
  modelsTitle: "Les modèles testés",
  modelsCols: { model: "Modèle", maker: "Éditeur", access: "Accès", size: "Taille", methods: "Configurations" },
  access: { api: "API (en ligne)", local: "Poids ouverts, exécuté localement" },
  limitsTitle: "Limites",
  limits: [
    "Une seule annotatrice : les notes reflètent une variété de kabyle et des choix d'orthographe. Plusieurs références par test limitent ce biais sans le supprimer.",
    "41 tests publics : les fourchettes sont larges, et les petits écarts entre modèles ne sont pas significatifs. Les scores par catégorie (2 à 4 tests hors traduction) sont indicatifs.",
    "Les 11 tests privés n'ont pas été utilisés ici : les offres gratuites des API peuvent réutiliser les requêtes, seuls les tests publics leur ont été envoyés.",
    "Deux réponses n'ont jamais pu être obtenues (un modèle qui tourne en boucle, une limite de quota) : elles sont comptées avec la note 1.",
    "Une partie des modèles a été évaluée avant la correction d'une faute de frappe dans deux consignes (version 1.0.1) ; la note n'en a pas tenu compte.",
    "Les modèles évoluent vite : les résultats valent pour les versions et la date indiquées.",
  ],
  reproduceTitle: "Tout est ouvert",
  reproduceBody: "Code, jeu de test public, données préparées, notebooks d'entraînement et résultats bruts sont publiés sur GitHub : chaque chiffre de ce site peut être vérifié et refait.",
  repo: "Voir le code sur GitHub",

  // ── Commun ──
  method: { base: "Seul", fewshot: "Few-shot", rag: "RAG", finetuned: "Fine-tuning" } as Record<string, string>,
  pending: "Résultats à venir",
  pendingBody: "Aucun chiffre n'est affiché avant d'avoir été mesuré.",
  footer: "Projet open source de",
  thanks: "Tanemmirt !",
  thanksBody: "Merci d'avoir lu jusqu'ici.",
  license: "Code : Apache-2.0 · Données : CC BY 4.0",
  points: "pts",

  // ── Habillage ──
  announce: ["41 tests écrits par une locutrice native", "15 configurations de modèles", "615 réponses notées à l'aveugle"],
  onThisPage: "Sur cette page",
  sections: {
    results: [
      ["classement", "Classement"],
      ["aides", "Apport des aides"],
      ["progression", "Progression"],
      ["categories", "Par catégorie"],
      ["accord", "Note automatique"],
    ],
    method: [
      ["jeu-de-test", "Jeu de test"],
      ["protocole", "Protocole"],
      ["aides", "Aides"],
      ["modeles", "Modèles"],
      ["glossaire", "Glossaire"],
      ["limites", "Limites"],
    ],
  } as Record<string, [string, string][]>,
  eyebrows: {
    kpi: "En chiffres",
    findings: "Synthèse",
    podium: "Classement",
    why: "Taqbaylit",
  },
  footAbout:
    "Un benchmark ouvert pour mesurer ce que les modèles de langage savent du kabyle, et ce qu'on peut leur apprendre.",
  footSite: "Le site",
  footProject: "Le projet",
  footCode: "Code source",
  footData: "Résultats bruts (JSON)",
  footAuthor: "L'autrice",
  footMade: "Fait avec soin pour la Kabylie",
};

export interface FindingValues {
  bestLabel: string;
  bestPct: string;
  fewshotLarge: string;
  fewshotLargeLabels: string;
  smallLabels: string;
  smallBase: string;
  ftLabel: string;
  ftBefore: string;
  ftAfter: string;
  ftBeats: string;
}

export type Dict = typeof fr;

const en: Dict = {
  siteName: "Kabyle LLM Benchmark",
  nav: { home: "Home", results: "Results", answers: "Answers", method: "Method" },
  pageTitle: {
    home: "Do AI models speak Kabyle?",
    results: "Results",
    answers: "Compare the answers",
    method: "Method",
  },
  description:
    "An open benchmark of how well language models handle Kabyle (Taqbaylit), blind-graded by a native speaker, and a measurement of what few-shot, RAG and fine-tuning add.",
  switchLang: "Français",
  theme: "Toggle theme",
  menu: "Menu",
  locale: "en-US",

  greeting: "Azul!",
  heroTitle: "Do AI models speak Kabyle?",
  heroLead:
    "15 language-model configurations, 41 tests written by a native speaker, 615 answers graded blind. What models really know about Kabyle, and what we can teach them.",
  heroCta: "See the results",
  heroCta2: "Read the answers",
  kpi: {
    best: "best score, with no help at all",
    gain: "largest improvement, from fine-tuning",
    graded: "answers graded by hand, blind",
    tests: "tests across 6 categories",
  },
  findingsTitle: "Key takeaways",
  findings: (v) => [
    { h: "Only one model already knows Kabyle", p: `${v.bestLabel} reaches ${v.bestPct}% with no help. No other model comes close, even with the best help.` },
    { h: "For large models, 5 examples are enough", p: `Adding a few translated sentences to the prompt (few-shot) gains ${v.fewshotLarge} points for ${v.fewshotLargeLabels}. It is the simplest and most effective help for them.` },
    { h: "Small models start from zero", p: `${v.smallLabels} score ${v.smallBase}: they answer in another language, or make up Kabyle-looking words.` },
    { h: "Fine-tuning transforms a small model", p: `Trained on Kabyle–French pairs, ${v.ftLabel} goes from ${v.ftBefore}% to ${v.ftAfter}%. It then beats much larger models used without help: ${v.ftBeats}.` },
    { h: "Conversation remains the weak spot", p: "Translation is within reach of the best models. Holding a natural conversation in Kabyle is not, for any of them: it is the lowest category everywhere." },
  ],
  homeTopTitle: "The podium",
  homeTopMore: "Full leaderboard",
  whyTitle: "Why Kabyle?",
  whyBody: [
    "Kabyle (Taqbaylit) is a Berber language spoken by several million people in Kabylia, northern Algeria, and by a large diaspora, especially in France. It is mostly written in the Latin script, with specific letters such as ɛ, ɣ, ḥ or ṭ, and also in Tifinagh (ⵜⵉⴼⵉⵏⴰⵖ).",
    "It is a low-resource language: little digital text, few tools, variable spelling. Language models, trained mostly on English, often confuse it with Arabic, French or other Berber languages.",
  ],
  facts: [
    { value: "≈ 7,200", label: "articles on Kabyle Wikipedia" },
    { value: "≈ 94,000", label: "Kabyle–French sentence pairs on Tatoeba" },
  ],

  resultsLead:
    "Every grade is given by hand, from 0 to 3, without knowing which model answered, then converted to a percentage. Ranges show the 95% uncertainty margin.",
  filterAll: "All",
  filterBase: "Models alone",
  filterHelped: "With help",
  rankingTitle: "Overall leaderboard",
  colModel: "Model",
  colMethod: "Help",
  colScore: "Score",
  colRange: "Score and 95% range",
  colChrf: "chrF++",
  colN: "Answers",
  matrixTitle: "What each kind of help adds",
  matrixLead: "Each row is a model, each column a way to help it. The gain is measured test by test against the model alone.",
  matrixNotTested: "not tested",
  matrixNotApplicable: "not possible",
  matrixNaNote: "Fine-tuning is only possible for open-weight models: Gemini and Mistral Large 4 do not allow it.",
  gainsChartTitle: "From the model alone to the helped model",
  gainsChartLead: "The grey dot is the model alone; each colored mark is the same model with one kind of help.",
  categoriesTitle: "By category",
  categoriesLead:
    "Few tests per category (see the count under each heading): these scores show a trend, not a ranking.",
  testsCount: (n) => `${n} test${n > 1 ? "s" : ""}`,
  agreementTitle: "Does the automatic score agree with the human grade?",
  agreementBody: (rho, n) =>
    `Spearman rank correlation of ${rho} between the human grade and chrF++ over ${n} answers: strong agreement. The automatic metric ranks answers in the same direction as the native speaker, but cannot replace her: it does not understand meaning.`,
  metaLine: (version, hash, date) => `Test set ${version} · SHA-256 ${hash}… · results exported on ${date}`,

  answersLead:
    "Pick a test to read the answers of all 15 configurations, with the grade each received. References are the author's; model answers are published as-is.",
  pickCategory: "Category",
  allCategories: "All",
  pickTest: "Test",
  search: "Search the prompts…",
  sortBy: "Sort by",
  sortScore: "grade",
  sortModel: "model",
  context: "Text",
  prompt: "Prompt",
  source: "Text to translate",
  references: "Author's reference",
  answer: "Answer",
  noAnswer: "No answer",
  score: "Grade",
  showMore: "Show all",
  showLess: "Collapse",
  scoreScale: ["Wrong or other language", "Partly correct", "Correct, minor errors", "Correct and natural"],

  methodLead: "How the benchmark was built, what the numbers mean, and what they do not say.",
  testsetTitle: "The test set",
  testsetBody: (pub, priv) => [
    "Every Kabyle text in the test set (references, comprehension texts, prompts written in Kabyle) is handwritten by a native speaker. None is AI-generated.",
    `The set has ${pub + priv} tests: ${pub} public ones, used for these results, and ${priv} kept private for future evaluations safe from any leak into training data.`,
  ],
  categoryDescriptions: {
    translation_fr_kab: "Translate a sentence from French into Kabyle.",
    translation_kab_fr: "Translate a sentence from Kabyle into French.",
    comprehension: "Read a short Kabyle text and answer a question about it.",
    culture: "Answer a question about Kabyle culture and traditions.",
    writing: "Write in Kabyle, in the Latin script or in Tifinagh.",
    conversation: "Reply naturally to a line, as in a conversation.",
  },
  protocolTitle: "Protocol",
  protocol: [
    { h: "Same prompt for all", p: "Every model receives exactly the same prompt, no system message, temperature 0. Each answer is stored with its exact parameters." },
    { h: "Blind grading", p: "Answers are drawn at random across all models. The author grades without knowing which model answered; the model is revealed only after grading." },
    { h: "No leakage", p: "Few-shot examples, the RAG index and training data are checked automatically: no sentence from the test set appears in them." },
  ],
  scaleTitle: "Grading scale",
  methodsTitle: "The three kinds of help",
  methods: [
    { id: "fewshot", h: "Few-shot", p: "5 Kabyle–French sentence pairs, the closest to the question in the Tatoeba corpus, are added to the prompt." },
    { id: "rag", h: "RAG (retrieval-augmented)", p: "At answer time, the model receives the 8 passages closest to the question, found by semantic search (bge-m3) in a Kabyle–French corpus." },
    { id: "finetuned", h: "Fine-tuning (QLoRA)", p: "The model is lightly retrained on tens of thousands of Kabyle–French pairs, on a free GPU. Only possible for open-weight models." },
  ],
  glossaryTitle: "Glossary",
  glossary: [
    { t: "Human score", d: "Mean hand-given grade (0 to 3), scaled to 100: 2.4 / 3 is 80%. It is the main measure." },
    { t: "95% range", d: "With 41 tests, a score is approximate. The range gives where the model's true level very likely lies (bootstrap). If two ranges largely overlap, the gap is not significant." },
    { t: "Gain (points)", d: "Difference between the helped model's score and the model alone, measured on the same tests. +38 points: from 37% to 75%." },
    { t: "chrF++", d: "Automatic score (0 to 100) comparing the answer to the reference character by character and word by word. Useful as a check, but it does not understand meaning: a good translation phrased differently is penalized." },
    { t: "Model alone (base)", d: "The model as is, with the plain prompt." },
    { t: "Open weights", d: "A downloadable model you can run on your own machine and retrain. Here: Qwen3.5 4B and Ministral 3 8B." },
  ],
  modelsTitle: "Models tested",
  modelsCols: { model: "Model", maker: "Maker", access: "Access", size: "Size", methods: "Configurations" },
  access: { api: "API (online)", local: "Open weights, run locally" },
  limitsTitle: "Limitations",
  limits: [
    "A single annotator: grades reflect one variety of Kabyle and particular spelling choices. Several references per test reduce this bias without removing it.",
    "41 public tests: ranges are wide, and small gaps between models are not significant. Per-category scores (2 to 4 tests outside translation) are indicative.",
    "The 11 private tests were not used here: free API tiers may reuse requests, so only public tests were sent to them.",
    "Two answers could never be obtained (a model stuck in a loop, a quota limit): they are counted with grade 1.",
    "Some models were evaluated before a typo was fixed in two prompts (version 1.0.1); grading did not penalize it.",
    "Models change fast: results hold for the versions and date shown.",
  ],
  reproduceTitle: "Everything is open",
  reproduceBody: "Code, public test set, prepared data, training notebooks and raw results are published on GitHub: every number on this site can be checked and reproduced.",
  repo: "See the code on GitHub",

  method: { base: "Alone", fewshot: "Few-shot", rag: "RAG", finetuned: "Fine-tuning" },
  pending: "Results coming soon",
  pendingBody: "No number is shown before it has been measured.",
  footer: "Open-source project by",
  thanks: "Tanemmirt!",
  thanksBody: "Thank you for reading.",
  license: "Code: Apache-2.0 · Data: CC BY 4.0",
  points: "pts",

  announce: ["41 tests written by a native speaker", "15 model configurations", "615 answers graded blind"],
  onThisPage: "On this page",
  sections: {
    results: [
      ["classement", "Leaderboard"],
      ["aides", "What helps"],
      ["progression", "Progress"],
      ["categories", "By category"],
      ["accord", "Automatic metric"],
    ],
    method: [
      ["jeu-de-test", "Test set"],
      ["protocole", "Protocol"],
      ["aides", "Methods"],
      ["modeles", "Models"],
      ["glossaire", "Glossary"],
      ["limites", "Limitations"],
    ],
  },
  eyebrows: {
    kpi: "Key figures",
    findings: "Summary",
    podium: "Leaderboard",
    why: "Taqbaylit",
  },
  footAbout: "An open benchmark measuring what language models know about Kabyle, and what they can be taught.",
  footSite: "The site",
  footProject: "The project",
  footCode: "Source code",
  footData: "Raw results (JSON)",
  footAuthor: "The author",
  footMade: "Made with care for Kabylie",
};

export const t: Record<Lang, Dict> = { fr, en };

/** Informations éditoriales sur chaque famille de modèles (non présentes dans l'export). */
/** Taille en milliards de paramètres ; null = non publiée par l'éditeur. */
export const MODEL_INFO: Record<string, { maker: string; params: number | null }> = {
  "gemini-flash": { maker: "Google", params: null },
  "gemini-flash-lite": { maker: "Google", params: null },
  "mistral-large-4": { maker: "Mistral AI", params: null },
  "ministral3-8b": { maker: "Mistral AI", params: 8 },
  "qwen3.5-4b": { maker: "Alibaba (Qwen)", params: 4 },
};

export const sizeLabel = (params: number | null, lang: Lang) =>
  params === null ? (lang === "fr" ? "non publiée" : "not disclosed") : lang === "fr" ? `${params} milliards` : `${params} billion`;

export const href = (base: string, page: PageId, lang: Lang) => `${base}${ROUTES[page][lang]}`;
