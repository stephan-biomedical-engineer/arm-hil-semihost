#!/bin/bash

# Cores para o terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}    ARM HIL Framework - Teste Local Automatizado ${NC}"
echo -e "${BLUE}=================================================${NC}\n"

# Verifica se o diretório do projeto foi passado como argumento
if [ -z "$1" ]; then
    # Se não passou argumento, assume o diretório atual
    APP_PATH="."
else
    APP_PATH="$1"
fi

# Converte para caminho absoluto para facilitar
cd "$APP_PATH" || { echo -e "${RED}[!] ERRO: Diretório '$APP_PATH' não encontrado.${NC}"; exit 1; }
ABS_APP_PATH=$(pwd)

echo -e "[*] Diretório do projeto: ${YELLOW}$ABS_APP_PATH${NC}"

# Detecta o sistema de build
if [ -f "CMakeLists.txt" ]; then
    echo -e "[*] Sistema de build detectado: ${GREEN}CMake${NC}\n"
    
    # Executa a sequência do CMake
    echo -e ">>> ${YELLOW}Passo 1/3: Limpando build antigo...${NC}"
    rm -rf build/
    
    echo -e "\n>>> ${YELLOW}Passo 2/3: Configurando CMake para testes HIL...${NC}"
    # Verifica se existe um preset Debug (padrão do CubeMX mais recente)
    if grep -q "Debug" CMakePresets.json 2>/dev/null; then
        cmake --preset Debug -DENABLE_HIL_TESTS=ON
        BUILD_CMD="cmake --build --preset Debug --target flash_test -j$(nproc)"
    else
        # Fallback para CMake antigo sem presets
        cmake -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_HIL_TESTS=ON
        BUILD_CMD="cmake --build build --target flash_test -j$(nproc)"
    fi
    
    # Verifica se a configuração funcionou
    if [ $? -ne 0 ]; then
        echo -e "\n${RED}[!] ERRO: Falha na configuração do CMake.${NC}"
        exit 1
    fi
    
    echo -e "\n>>> ${YELLOW}Passo 3/3: Compilando e executando testes...${NC}"
    eval $BUILD_CMD

elif [ -f "Makefile" ]; then
    echo -e "[*] Sistema de build detectado: ${GREEN}Makefile${NC}\n"
    
    # Executa a sequência do Make
    echo -e ">>> ${YELLOW}Passo 1/2: Limpando build antigo...${NC}"
    make clean
    
    echo -e "\n>>> ${YELLOW}Passo 2/2: Compilando e executando testes...${NC}"
    make ENABLE_HIL=1 flash_test -j$(nproc)

else
    echo -e "${RED}[!] ERRO: Nenhum sistema de build (CMake ou Makefile) detectado na pasta.${NC}"
    echo "    Certifique-se de estar na raiz do projeto STM32."
    exit 1
fi

# Verifica o resultado final da execução (compilação + python)
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}=================================================${NC}"
    echo -e "${GREEN}    Processo de Teste Local Concluído!           ${NC}"
    echo -e "${GREEN}=================================================${NC}"
else
    echo -e "\n${RED}=================================================${NC}"
    echo -e "${RED}    Falha durante a execução ou compilação!      ${NC}"
    echo -e "${RED}=================================================${NC}"
    exit 1
fi
