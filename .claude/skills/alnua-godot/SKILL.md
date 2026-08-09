# /alnua-godot — Godot MCP + Nova (Dev Gaming)

Skill pour Nova Fischer (dev_gaming_agent) dans le Gaming Studio.
Godot 4 + GDScript via godot-mcp. UE5.8 (serveur Hub, DEC-017) est un chemin
parallèle — ce skill couvre **uniquement** Godot ; ne pas mélanger les outils.

---

## Quand utiliser ce skill

- Développement de mécaniques de jeu Godot 4 (GDScript / C#)
- Debugging via godot-mcp depuis Cursor
- Nova (dev_gaming) génère du GDScript → test direct dans Godot
- Mira (game_director) valide le GDD → Nova implémente

---

## MCP godot-mcp — Configuration

Le MCP godot-mcp tourne dans Cursor via `.cursor/mcp.json` :

```json
{
  "mcpServers": {
    "godot": {
      "command": "npx",
      "args": ["-y", "godot-mcp@latest"],
      "env": {
        "GODOT_PROJECT_PATH": "/chemin/absolu/vers/projet.godot"
      }
    }
  }
}
```

**Installation préalable :**
```bash
npm install -g godot-mcp
# Godot 4.x doit être dans le PATH ou GODOT_PATH défini
```

**Outils MCP disponibles (après connexion) :**
- `godot_run_script` — Exécute GDScript dans la scène active
- `godot_get_node` — Récupère un nœud par chemin (ex: `"res://scenes/Player.tscn"`)
- `godot_set_property` — Modifie une propriété de nœud
- `godot_list_nodes` — Liste l'arborescence de la scène
- `godot_eval` — Évalue une expression GDScript
- `godot_screenshot` — Screenshot du viewport Godot

---

## Pattern Nova — Endpoint API

```python
# Nova génère du GDScript via l'API Hub
POST /agents/dev-gaming/handle

Body:
{
  "instruction": "Crée un système de double saut avec coyote time de 0.15s"
}

# Nova retourne GDScript structuré :
{
  "implementation": {
    "script": "extends CharacterBody2D\n...",
    "scene_modifications": [...],
    "test_steps": [...]
  }
}
```

---

## Patterns GDScript ALNUA

### Mécanique de base (Godot 4)
```gdscript
extends CharacterBody2D

const SPEED = 300.0
const JUMP_VELOCITY = -400.0
const COYOTE_TIME = 0.15
const JUMP_BUFFER = 0.1

var coyote_timer := 0.0
var jump_buffer_timer := 0.0
var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")

func _physics_process(delta: float) -> void:
    # Gravity
    if not is_on_floor():
        velocity.y += gravity * delta
        coyote_timer -= delta
    else:
        coyote_timer = COYOTE_TIME

    # Jump buffer
    if Input.is_action_just_pressed("jump"):
        jump_buffer_timer = JUMP_BUFFER
    jump_buffer_timer -= delta

    # Jump avec coyote time + buffer
    if jump_buffer_timer > 0 and coyote_timer > 0:
        velocity.y = JUMP_VELOCITY
        coyote_timer = 0.0
        jump_buffer_timer = 0.0

    # Mouvement horizontal
    var direction := Input.get_axis("move_left", "move_right")
    velocity.x = direction * SPEED if direction else move_toward(velocity.x, 0, SPEED)
    move_and_slide()
```

### Signal pattern (découplage)
```gdscript
# Toujours utiliser des signaux pour découpler les systèmes
signal health_changed(new_health: int, delta: int)
signal player_died

var health := 100:
    set(value):
        var delta = value - health
        health = clampi(value, 0, max_health)
        health_changed.emit(health, delta)
        if health == 0:
            player_died.emit()
```

### Autoload (Singleton pattern)
```gdscript
# GameManager.gd — dans Project Settings > Autoload
extends Node

signal score_changed(new_score: int)
var score := 0

func add_score(points: int) -> void:
    score += points
    score_changed.emit(score)
```

---

## Pipeline Mira → Nova

```
Mira (game_director) → POST /agents/game-director/game-concept
                      ↓ game_concept JSON
Nova (dev_gaming)   → POST /agents/dev-gaming/handle
                      ↓ GDScript + scene structure
```

**Commande Cursor directe :**
```
/alnua-agents → chercher Nova (dev_gaming)
POST /agents/dev-gaming/handle {"instruction": "..."}
```

---

## Règles Nova

- **Jamais UE5** — Godot 4 uniquement
- GDScript préféré au C# (sauf si perf critique)
- Toujours inclure `test_steps` dans la réponse
- Pattern signal pour tout event inter-systèmes
- `@export` pour tout paramètre ajustable depuis l'Inspector
- `delta` sur toute logique frame-dépendante

---

## Commandes MCP utiles depuis Cursor

```
# Tester une mécanique sans relancer Godot
<tool:godot_run_script>
extends SceneTree
func _init():
    var player = preload("res://scenes/Player.tscn").instantiate()
    print(player.SPEED)
    quit()
</tool:godot_run_script>

# Vérifier la scène active
<tool:godot_list_nodes>{}
</tool:godot_list_nodes>
```

---

## Troubleshooting godot-mcp

| Erreur | Cause | Fix |
|--------|-------|-----|
| `GODOT_PROJECT_PATH not set` | Variable d'env manquante | Ajouter dans `.cursor/mcp.json` env |
| `Godot not found` | Godot pas dans PATH | `export GODOT_PATH=/usr/bin/godot4` |
| `Cannot connect to Godot` | Godot fermé | Ouvrir le projet dans l'éditeur Godot |
| `Script parse error` | GDScript invalide | Vérifier syntaxe GD4 (pas GD3) |
