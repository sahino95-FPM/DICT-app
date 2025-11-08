# Script PowerShell pour initialiser la base de données FPMsigm
# Auteur: FPM DICT
# Date: Novembre 2024

Write-Host "============================================" -ForegroundColor Green
Write-Host "Initialisation de la base de donnees FPMsigm" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Vérifier que le fichier SQL existe
if (-not (Test-Path "init_db.sql")) {
    Write-Host "ERREUR: Le fichier init_db.sql n'existe pas!" -ForegroundColor Red
    Write-Host "Assurez-vous d'etre dans le bon repertoire." -ForegroundColor Yellow
    exit 1
}

# Demander le mot de passe MySQL
$password = Read-Host "Entrez le mot de passe root MySQL" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$mysqlPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

Write-Host ""
Write-Host "Connexion a MySQL et execution du script..." -ForegroundColor Cyan
Write-Host ""

# Exécuter le script SQL
try {
    Get-Content init_db.sql | mysql -u root -p"$mysqlPassword" 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "============================================" -ForegroundColor Green
        Write-Host "Base de donnees initialisee avec succes!" -ForegroundColor Green
        Write-Host "============================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Vous pouvez maintenant lancer l'application:" -ForegroundColor Cyan
        Write-Host "  python run.py" -ForegroundColor Yellow
        Write-Host ""
    } else {
        throw "Erreur lors de l'execution du script SQL"
    }
} catch {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "ERREUR lors de l'initialisation!" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifiez:" -ForegroundColor Yellow
    Write-Host "- MySQL est bien installe et demarre" -ForegroundColor Yellow
    Write-Host "- Le mot de passe root est correct" -ForegroundColor Yellow
    Write-Host "- Le fichier init_db.sql existe" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Erreur: $_" -ForegroundColor Red
    exit 1
}

# Nettoyer le mot de passe de la mémoire
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

Write-Host "Appuyez sur une touche pour continuer..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
