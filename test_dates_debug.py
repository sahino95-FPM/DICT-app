"""Script pour vérifier les dates des lignes"""
from app import create_app
from app.models.scenario2 import Scenario2Model

app = create_app()

with app.app_context():
    num_pec = '25M001940/0098Q'

    # Vérifier les dates des lignes RUB
    query = """
    SELECT
        MIN(lrh.date_execution_acte) as date_min,
        MAX(lrh.date_execution_acte) as date_max,
        COUNT(*) as nb_lignes
    FROM acte_trans at
    JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans
    WHERE at.num_pec LIKE :num_pec
    """
    result = Scenario2Model.execute_query(query, {'num_pec': f'%{num_pec}%'})
    print(f"Dates des lignes RUB:")
    print(f"  Date MIN: {result[0]['date_min']}")
    print(f"  Date MAX: {result[0]['date_max']}")
    print(f"  Nb lignes: {result[0]['nb_lignes']}")

    # Compter combien de lignes sont dans la période 2015-11-11 au 2025-11-08
    query_periode = """
    SELECT COUNT(*) as nb_lignes_periode
    FROM acte_trans at
    JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans
    WHERE at.num_pec LIKE :num_pec
      AND lrh.date_execution_acte BETWEEN '2015-11-11' AND '2025-11-08'
    """
    result_periode = Scenario2Model.execute_query(query_periode, {'num_pec': f'%{num_pec}%'})
    print(f"\nLignes dans la période 2015-11-11 → 2025-11-08: {result_periode[0]['nb_lignes_periode']}")

    # Lister les lignes HORS période
    query_hors_periode = """
    SELECT
        lrh.date_execution_acte,
        lrh.montant,
        lrh.qte,
        (lrh.montant * lrh.qte) as total,
        COALESCE(a2.libelle_acte, rh.libelle) as libelle
    FROM acte_trans at
    JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans
    LEFT JOIN acte a2 ON a2.id_acte = lrh.id_acte
    LEFT JOIN rubrique_hospitalisations rh ON rh.id = lrh.id_rub_hospit
    WHERE at.num_pec LIKE :num_pec
      AND (lrh.date_execution_acte < '2015-11-11' OR lrh.date_execution_acte > '2025-11-08')
    """
    result_hors = Scenario2Model.execute_query(query_hors_periode, {'num_pec': f'%{num_pec}%'})

    if result_hors:
        print(f"\n⚠️  {len(result_hors)} ligne(s) HORS période:")
        for row in result_hors:
            print(f"  - Date: {row['date_execution_acte']}, Libellé: {row['libelle']}, Total: {row['total']}")
    else:
        print("\n✓ Toutes les lignes sont dans la période")
