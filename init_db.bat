@echo off
echo ============================================
echo Initialisation de la base de donnees FPMsigm
echo ============================================
echo.

REM Demander le mot de passe MySQL
set /p MYSQL_PASSWORD="Entrez le mot de passe root MySQL: "

echo.
echo Connexion a MySQL et execution du script...
echo.

mysql -u root -p%MYSQL_PASSWORD% < init_db.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo Base de donnees initialisee avec succes!
    echo ============================================
    echo.
    echo Vous pouvez maintenant lancer l'application:
    echo   python run.py
    echo.
) else (
    echo.
    echo ============================================
    echo ERREUR lors de l'initialisation!
    echo ============================================
    echo.
    echo Verifiez:
    echo - MySQL est bien installe et demarre
    echo - Le mot de passe root est correct
    echo - Le fichier init_db.sql existe
    echo.
)

pause
