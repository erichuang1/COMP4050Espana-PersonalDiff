@REM You could also try `rd /s /q`
if exist "_internalRepo\" (
	rmdir /s /q "_internalRepo"	:: win10 works?
	rm -rf _internalRepo		:: win11 works?
)

git init _internalRepo
cd _internalRepo
git remote add origin "https://github.com/COMP4050TeamWide/Capote_AI.git"
git config core.sparseCheckout true

echo src/capote_ai > .git/info/sparse-checkout

git fetch origin main
git checkout main
git config core.sparseCheckout false
cd ..

:: src files
:: "_internalRepo\src\capote_ai\viva_questions.py"
:: "_internalRepo\src\capote_ai\rubric_gen.py"
:: "_internalRepo\src\capote_ai\pdf_to_text.py" 
:: "_internalRepo\src\capote_ai\grammar_check.py" 
:: dest folder
:: "Backend\server\src\ai"

copy "_internalRepo\src\capote_ai\viva_questions.py" "Backend\server\src\ai"
copy "_internalRepo\src\capote_ai\rubric_gen.py" "Backend\server\src\ai"
copy "_internalRepo\src\capote_ai\pdf_to_text.py" "Backend\server\src\ai"
copy "_internalRepo\src\capote_ai\grammar_check.py" "Backend\server\src\ai"

timeout 5

if exist "_internalRepo\" (
	rmdir /s /q "_internalRepo"	:: win10 works?
	rm -rf "_internalRepo" 		:: win11 works?
)