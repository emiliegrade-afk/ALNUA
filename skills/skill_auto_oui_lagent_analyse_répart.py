import requests
from datetime import datetime
from typing import Dict, List, Any

def skill_auto_oui_lagent_analyse_répart(api_key: str = None, hub_url: str = "https://api.hub.alnua.com", 
                                       include_briefing: bool = True, auto_assign: bool = False) -> Dict[str, Any]:
    """
    Analyse automatique des projets et répartition des tâches sur le Hub ALNUA.
    
    Cette fonction récupère les données des projets actifs, analyse leur état,
    identifie les problèmes et propose une répartition des tâches.
    
    Args:
        api_key (str, optional): Clé d'authentification API Hub
        hub_url (str): URL de base de l'API Hub
        include_briefing (bool): Inclure le briefing quotidien dans l'analyse
        auto_assign (bool): Assigner automatiquement les tâches (nécessite permissions)
    
    Returns:
        Dict contenant l'analyse complète et les recommandations de répartition
    """
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "analysis": {},
        "briefing": {},
        "repartition": [],
        "errors": [],
        "recommendations": []
    }
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["Content-Type"] = "application/json"
    
    try:
        # 1. Récupération du briefing quotidien
        if include_briefing:
            try:
                briefing_response = requests.get(f"{hub_url}/briefing/daily", headers=headers, timeout=10)
                if briefing_response.status_code == 200:
                    briefing_data = briefing_response.json()
                    result["briefing"] = {
                        "projets_actifs": briefing_data.get("active_projects", 0),
                        "tickets_urgents": briefing_data.get("urgent_tickets", 0),
                        "erreurs_non_resolues": briefing_data.get("unresolved_errors", 0),
                        "status": "✅ Récupéré"
                    }
                else:
                    result["briefing"]["status"] = f"⚠️ Erreur {briefing_response.status_code}"
            except Exception as e:
                result["briefing"]["status"] = f"❌ Échec: {str(e)}"
        
        # 2. Analyse des projets
        try:
            projects_response = requests.get(f"{hub_url}/projects", headers=headers, timeout=10)
            
            if projects_response.status_code == 401:
                result["status"] = "blocked"
                result["errors"].append("Problème d'authentification API Hub (401)")
                result["recommendations"].append("Vérifier la configuration de la clé API Hub")
                result["analysis"]["status"] = "❌ Bloquée - Authentification requise"
                return result
            
            elif projects_response.status_code == 200:
                projects = projects_response.json()
                result["analysis"] = _analyser_projets(projects)
                result["repartition"] = _generer_repartition(projects, auto_assign)
                
            else:
                result["errors"].append(f"Erreur API projets: {projects_response.status_code}")
                result["analysis"]["status"] = f"❌ Erreur {projects_response.status_code}"
                
        except requests.exceptions.RequestException as e:
            result["errors"].append(f"Erreur réseau: {str(e)}")
            result["analysis"]["status"] = "❌ Erreur de connexion"
        
        # 3. Génération des recommandations finales
        result["recommendations"].extend(_generer_recommandations(result))
        
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Erreur générale: {str(e)}")
    
    return result

def _analyser_projets(projects: List[Dict]) -> Dict[str, Any]:
    """Analyse les projets et identifie les problèmes."""
    
    analysis = {
        "total_projets": len(projects),
        "projets_actifs": 0,
        "projets_en_retard": 0,
        "projets_critiques": 0,
        "charge_totale": 0,
        "problemes_identifies": [],
        "status": "✅ Analysé"
    }
    
    for project in projects:
        if project.get("status") == "active":
            analysis["projets_actifs"] += 1
            
        # Vérification des retards
        if project.get("deadline") and project.get("progress", 0) < 80:
            deadline = datetime.fromisoformat(project["deadline"].replace('Z', '+00:00'))
            if deadline < datetime.now():
                analysis["projets_en_retard"] += 1
                analysis["problemes_identifies"].append(f"Projet {project.get('name', 'N/A')} en retard")
        
        # Identification des projets critiques
        if project.get("priority") == "critical" or project.get("errors", 0) > 0:
            analysis["projets_critiques"] += 1
            
        # Calcul de la charge
        analysis["charge_totale"] += project.get("workload", 0)
    
    return analysis

def _generer_repartition(projects: List[Dict], auto_assign: bool = False) -> List[Dict]:
    """Génère les recommandations de répartition des tâches."""
    
    # Ce module semble être une “placeholder” générationnelle.
    # Pour la stabilité (migration VPS), on le rend volontairement inoffensif :
    # - pas d'assignation automatique
    # - retourne une structure vide si on ne sait pas répartir.
    _ = auto_assign  # reserved for future
    repartition: List[Dict[str, Any]] = []
    for project in projects:
        repartition.append(
            {
                "project": project.get("name") or project.get("id") or "",
                "recommendations": [],
            }
        )
    return repartition


def _generer_recommandations(result: Dict[str, Any]) -> List[str]:
    """Fallback minimal pour éviter tout crash si le skill est appelé."""
    _ = result
    return []