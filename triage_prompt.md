You are screening new arXiv papers for one physicist. For each paper below you
see only the title, authors, categories and abstract. Decide how relevant each
paper is to this reader's research interests and return a score for EVERY paper.

These papers were NOT caught by the reader's author and citation alerts, so
most of them are irrelevant. Your job is to find the few that the reader would
be sorry to miss. Expect roughly 1 paper in 15 to deserve a score of 2 or 3.
If you are scoring many more than that as 2 or 3, you are being too generous.

# The reader's interests

## Core topics (a paper squarely about one of these scores 3)

1. Multifield inflation dynamics: rapid-turn / strongly non-geodesic
   inflation, hyperbolic or curved field-space models, sidetracked / angular /
   hyperinflation, multifield attractors, turning trajectories, entropic
   (isocurvature) mass, stability of multifield backgrounds.
2. Inflation with many fields or random potentials: random-matrix / Dyson
   Brownian motion / Gaussian random field landscapes, statistical predictions
   of inflation in a landscape, universality or prior dependence of many-field
   predictions.
3. Swampland conjectures applied to cosmology: de Sitter conjecture, distance
   conjecture or TCC confronted with inflation, quintessence or dark energy;
   steep-potential or rapid-turn models built to satisfy swampland bounds;
   inflation in supergravity or string compactifications with explicit
   multifield dynamics.
4. LISA data analysis: global fit, time-delay interferometry (TDI), noise
   modelling and noise-agnostic methods, data gaps and glitches, instrument
   response, LISA pipeline software and mock data challenges.
5. Stochastic gravitational-wave background (SGWB) detection and spectral
   reconstruction with LISA or other space detectors: template-free or binned
   reconstruction, separating cosmological from astrophysical foregrounds,
   anisotropies of the background as seen by LISA.
6. New ways of detecting gravitational waves by timing or tracking, such as
   timing arrays built from sources other than pulsars.

## Adjacent topics (a paper squarely about one of these scores 2)

- Primordial non-Gaussianity or features in the power spectrum caused by
  multifield or heavy-field effects; cosmological collider signals;
  effective field theory of inflation with reduced sound speed from turns.
- Primordial black holes or scalar-induced gravitational waves produced by an
  inflationary mechanism (enhanced small-scale power, sharp turns, features).
- Cosmological gravitational-wave sources with a concrete forecast for LISA
  (first-order phase transitions, cosmic strings, inflationary GWs).
- String cosmology: moduli stabilisation, de Sitter constructions, axion
  monodromy or other string inflation models, when the paper makes
  cosmological statements (not purely formal constructions).
- Gravitational-wave data-analysis METHODS that would transfer to LISA:
  new samplers, trans-dimensional or global-fit techniques, simulation-based
  inference for GW signals, noise estimation, pulsar-timing-array analysis
  methods for stochastic backgrounds.
- Preheating / reheating after multifield inflation with non-minimal couplings.

# Scoring scale

- 3 = Directly about a core topic. The reader would want to read it this week.
- 2 = Squarely about an adjacent topic, or touches a core topic as a
      significant secondary part of the paper.
- 1 = Same broad field (inflation, string theory, cosmology, gravitational
      waves) but not about any topic listed above.
- 0 = Unrelated.

# Rules for scoring

- Judge what the paper actually DOES, not which words appear. A keyword
  appearing once in the abstract is not enough.
- When you are unsure between two scores, choose the LOWER one.
- Do not raise a score because the authors are famous or the result sounds
  important. Only relevance to the topics above matters.
- Review articles and lecture notes get the same score as a research paper on
  the same topic would.

Common mistakes to avoid (all of these are score 0 or 1, not 2 or 3):

- Single-field inflation model building, or yet another fit of an inflation
  model to CMB data (ACT, Planck, BICEP), with no multifield dynamics: score 1.
- Dark energy or modified gravity fitted to DESI / supernova data with no
  swampland or string theory content: score 1.
- A paper that just says its signal "could be detected by LISA" in the last
  sentence, without doing a LISA analysis or forecast: score 0 or 1.
- LIGO / Virgo / KAGRA event detections, catalogues, population studies,
  waveform modelling for compact binaries, tests of GR with ground-based
  detectors: score 1 at most, unless the paper's main point is a new analysis
  method that would transfer to LISA (then 2).
- Astrophysics of LISA sources (massive black hole binary populations, EMRI
  rates, galactic binaries formation) without a data-analysis component: 1.
- Pulsar timing array astrophysical interpretation (supermassive black hole
  binary populations, new-physics fits to the NANOGrav spectrum): score 1.
- Formal string theory, holography, amplitudes, black hole information, swampland
  conjectures discussed with no cosmological application: score 1.
- "Inflation" used in a non-cosmological sense, or "LISA" being a different
  acronym: score 0.
- Primordial black holes as dark matter constrained by observations, with no
  inflationary formation mechanism studied: score 1.

# Tags

For each paper also choose zero or more tags from exactly this list (copy them
character for character, do not invent new ones):

{{TAGS}}

Only add a tag when the paper is clearly about that subject. Papers scored 0
should get an empty tag list.

# Reason

For each paper write ONE sentence of at most 25 words saying what the paper
does and why that earned its score. Be specific to the paper. Do not start
with "This paper". Example of a good reason: "Derives the entropic mass for
rapid-turn trajectories on hyperbolic field space and finds a new stable
attractor." Example of a bad reason: "Relevant to inflation."

# Output

Return one result for each paper, in the same order as the input, using the
paper's "id" exactly as given. Do not skip any paper and do not add papers.

# Papers

{{PAPERS}}
