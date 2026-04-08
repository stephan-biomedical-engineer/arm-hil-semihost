#!/bin/bash

# Cores para o terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}    Instalador Automático: ARM HIL Framework     ${NC}"
echo -e "${BLUE}=================================================${NC}\n"

# 0. Verificação de Sanidade: Estamos em um projeto STM32/CMake ou STM32/Makefile?
if [ ! -f "CMakeLists.txt" ] && [ ! -f "Makefile" ]; then
    echo -e "${RED}[!] ERRO: Nenhum sistema de build (CMake ou Makefile) detectado!${NC}"
    echo "    Gere o projeto no STM32CubeMX primeiro."
    exit 1
fi

# 1. Gerenciamento de Git/Submódulo
if [ ! -d ".git" ]; then
    echo "[*] Inicializando repositório Git..."
    git init
fi

echo "[*] Configurando submódulo em hil_framework..."
if [ ! -d "hil_framework" ]; then
    git submodule add https://github.com/stephan-biomedical-engineer/arm-hil-semihost.git hil_framework
else
    echo "    Atualizando submódulo existente..."
    git submodule update --init --recursive
fi

# 2. Execução do Integrador Python
echo -e "\n[*] Acionando o integrador..."
if command -v python3 &>/dev/null; then
    # O 'if !' garante que se o python der erro, o bash para aqui
    if ! python3 hil_framework/hil_tool/setup_target.py --app .; then
        echo -e "${RED}[!] Falha na integração do CMake/YAML.${NC}"
        exit 1
    fi
else
    echo -e "${RED}[!] ERRO: python3 não encontrado.${NC}"
    exit 1
fi

echo -e "\n${GREEN}[OK] Instalação concluída com sucesso!${NC}"