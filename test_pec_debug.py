"""Script de diagnostic pour vérifier les lignes du dossier PEC"""
from app import create_app
from app.models.scenario2 import Scenario2Model

app = create_app()

with app.app_context():
    num_pec = '25M001940/0098Q'

    # Test 1: Compter les lignes RUB
    query_rub = """
    SELECT COUNT(*) as count, SUM(lrh.montant * lrh.qte) as total
    FROM acte_trans at
    JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans
    WHERE at.num_pec LIKE :num_pec
    """
    result_rub = Scenario2Model.execute_query(query_rub, {'num_pec': f'%{num_pec}%'})
    print(f"RUB - Lignes: {result_rub[0]['count']}, Total: {result_rub[0]['total']}")

    # Test 2: Compter les lignes ACTE
    query_acte = """
    SELECT COUNT(*) as count, SUM(laa.montant_acte * laa.quantite) as total
    FROM acte_trans at
    JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at.id_acte_trans
    WHERE at.num_pec LIKE :num_pec
    """
    result_acte = Scenario2Model.execute_query(query_acte, {'num_pec': f'%{num_pec}%'})
    print(f"ACTE - Lignes: {result_acte[0]['count']}, Total: {result_acte[0]['total']}")

    # Test 3: Total général
    query_total = """
    SELECT COUNT(*) as count, SUM(montant_total) as total
    FROM (
        SELECT lrh.montant * lrh.qte AS montant_total
        FROM acte_trans at
        JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans
        WHERE at.num_pec LIKE :num_pec

        UNION ALL

        SELECT laa.montant_acte * laa.quantite AS montant_total
        FROM acte_trans at
        JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at.id_acte_trans
        WHERE at.num_pec LIKE :num_pec
    ) AS lignes
    """
    result_total = Scenario2Model.execute_query(query_total, {'num_pec': f'%{num_pec}%'})
    print(f"TOTAL - Lignes: {result_total[0]['count']}, Montant: {result_total[0]['total']}")

    # Test 4: Vérifier la facture
    details = Scenario2Model.get_facture_details(num_pec)
    montant_facture = sum(float(item['montant']) if item['montant'] is not None else 0 for item in details)
    print(f"FACTURE - Lignes groupées: {len(details)}, Montant total: {montant_facture}")

    # Test 5: Vérifier avec la requête consolidée
    query_group = """
    WITH lignes AS (
        SELECT
            at.num_pec,
            lrh.montant * lrh.qte AS montant_total
        FROM acte_trans at
        JOIN list_rub_hosp_acte_trans lrh ON lrh.id_acte_trans = at.id_acte_trans
        WHERE at.num_pec LIKE :num_pec

        UNION ALL

        SELECT
            at.num_pec,
            laa.montant_acte * laa.quantite AS montant_total
        FROM acte_trans at
        JOIN list_acte_acte_trans laa ON laa.id_acte_trans = at.id_acte_trans
        WHERE at.num_pec LIKE :num_pec
    )
    SELECT
        num_pec,
        COUNT(*) as nb_lignes,
        SUM(montant_total) as montant_group_numpec
    FROM lignes
    GROUP BY num_pec
    """
    result_group = Scenario2Model.execute_query(query_group, {'num_pec': f'%{num_pec}%'})
    if result_group:
        print(f"GROUPÉ - Lignes: {result_group[0]['nb_lignes']}, Total cumulé PEC: {result_group[0]['montant_group_numpec']}")
