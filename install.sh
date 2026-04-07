#!/bin/bash

# Cores para deixar o terminal bonito
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}    Instalador Automático: ARM HIL Framework     ${NC}"
echo -e "${BLUE}=================================================${NC}\n"

# 1. Verifica se o usuário já tem um repositório Git
if [ ! -d ".git" ]; then
    echo "[*] Repositório Git não encontrado. Inicializando 'git init'..."
    git init
fi

# 2. Adiciona o submódulo
echo "[*] Baixando a ferramenta como submódulo em libs/hil_framework..."
# Se a pasta já existir, ele apenas atualiza
if [ ! -d "libs/hil_framework" ]; then
    git submodule add https://github.com/stephan-biomedical-engineer/arm-hil-semihost.git libs/hil_framework
else
    echo "    Submódulo já existe. Atualizando..."
    git submodule update --init --recursive
fi

# 3. Dispara a mágica do Python
echo -e "\n[*] Acionando o integrador (setup_target.py)..."
if command -v python3 &>/dev/null; then
    python3 libs/hil_framework/hil_tool/setup_target.py --app .
else
    echo "[!] ERRO: python3 não encontrado no sistema."
    exit 1
fi

echo -e "\n${GREEN}[OK] Instalação concluída com sucesso!${NC}"
echo "     -> Verifique o seu CMakeLists.txt"
echo "     -> Verifique a pasta .github/workflows/"
