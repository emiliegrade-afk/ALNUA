# SPEC — BrandKit AI intégré au Hub ALNUA

> Fichier de référence à copier à la racine de `c:\Dev\ALNUA_HUB\`
> Le fichier `.cursor/rules/brandkit.mdc` y fait référence.

## Objectif
Agent Brand Design intégré au Hub ALNUA. À partir d'une image uploadée :
1. Analyser l'identité visuelle (GPT-4V via OpenRouter)
2. Extraire palette K-means + bounding boxes des composants
3. Découper les assets avec OpenCV + rembg (fond transparent)
4. Générer 20 formats réseaux sociaux avec Pillow
5. Stocker dans Supabase (table brand_kits) + fichiers locaux par projet

## Architecture

```
c:\Dev\ALNUA_HUB\
├── agents/
│   └── brand_agent.py          ← orchestrateur CrewAI
├── services/
│   ├── vision_llm.py           ← appel GPT-4V (OpenRouter)
│   ├── palette.py              ← extraction K-means
│   ├── segmentation.py         ← OpenCV + rembg
│   └── kit_generator.py        ← Pillow → 20 formats
├── brand_kits/
│   ├── uploads/                ← images uploadées temporaires
│   ├── naïa/                   ← assets par projet
│   ├── wyrdheim/
│   ├── eve/
│   └── alnua_global/
├── SPEC_BRANDKIT_HUB.md        ← ce fichier
└── web/src/
    ├── app/brand/page.tsx
    └── components/brand/
```

## Modèles de données

### Pydantic (backend)

```python
class BoundingBox(BaseModel):
    x1: int  # 0-1000 normalisé
    y1: int
    x2: int
    y2: int

class BrandElement(BaseModel):
    label: str          # ex: "symbol", "wordmark", "tagline", "icon"
    type: str           # "symbol" | "text" | "combined"
    bbox: BoundingBox
    description: str

class ColorInfo(BaseModel):
    hex: str
    name: str           # ex: "Obsidienne"
    role: str           # "primary_bg" | "primary_accent" | "secondary" | "text"
    source: str         # "llm" | "kmeans" | "merged"

class BrandAnalysis(BaseModel):
    brand_name: str
    tagline: Optional[str]
    style: str
    mood: List[str]
    typography_style: str
    colors: List[ColorInfo]        # mergé LLM + K-means
    elements: List[BrandElement]   # avec bbox
    usage_notes: str
    components: dict               # has_symbol, has_wordmark, etc.
```

### Supabase (table brand_kits)
```sql
brand_kits (
  id uuid PK,
  project_id uuid FK → projects,
  brand_name text,
  analysis jsonb,        -- BrandAnalysis sérialisé
  assets_path text,      -- chemin local du dossier
  formats_generated text[], -- liste des formats créés
  created_at timestamptz,
  updated_at timestamptz
)
```

## Formats de sortie (20 formats)

| Catégorie | Fichier | Dimensions |
|---|---|---|
| **Profils** | instagram_profile.png | 320×320 |
| | tiktok_profile.png | 200×200 |
| | x_profile.png | 400×400 |
| | youtube_profile.png | 800×800 |
| | linkedin_profile.png | 300×300 |
| | favicon.png | 32×32 |
| | app_icon.png | 1024×1024 |
| **Bannières** | x_header.png | 1500×500 |
| | youtube_banner.png | 2560×1440 |
| | linkedin_banner.png | 1128×191 |
| | facebook_cover.png | 820×312 |
| **Posts** | instagram_post.png | 1080×1080 |
| | instagram_story.png | 1080×1920 |
| | tiktok_cover.png | 1080×1920 |
| **Assets isolés** | symbol_transparent.png | 1000×1000 (fond transparent) |
| | wordmark_transparent.png | 2000×500 (fond transparent) |
| | logo_dark_bg.png | 1000×1000 (fond couleur primaire) |
| | logo_light_bg.png | 1000×1000 (fond blanc) |
| | logo_horizontal.png | 2000×600 |
| **Report** | BRAND_KIT.md | — |

## Endpoints API

```
POST   /brand/analyze              → upload image → BrandAnalysis
POST   /brand/generate-kit         → BrandAnalysis → 20 formats
GET    /brand/kits                 → liste kits (project_id?)
GET    /brand/kits/:id             → kit complet
GET    /brand/kits/:id/download    → ZIP de tous les assets
POST   /brand/open-folder          → ouvre dossier dans explorateur
```

## Règles de pipeline
- Toujours redimensionner à 2048px max AVANT l'appel LLM
- LLM fournit les bbox (coordonnées normalisées 0-1000) → OpenCV exécute le crop pixel
- Ne jamais inverser : LLM = analyse/localisation, OpenCV = exécution pixel
- Valider BrandAnalysis avec Pydantic + 1 retry si parsing échoue
- Marge de 5% autour de chaque bbox avant crop
- rembg pour tous les assets isolés (symbol, wordmark)
- Palette finale = merge LLM colors + top 5 K-means (dédupliqué par proximité hex)

## Phases de développement

- **Phase 1** : Structure + upload + analyse LLM brute → JSON affiché
- **Phase 2** : Pydantic strict + K-means + palette mergée + ColorPalette UI
- **Phase 3** : Segmentation OpenCV + rembg → assets isolés + AssetGrid UI
- **Phase 4** : Kit generator (20 formats) + ZIP export + page /brand complète