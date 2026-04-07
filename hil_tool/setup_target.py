import os
import sys
import argparse

def setup_hil(app_path):
    app_path = os.path.normpath(app_path)
    project_name = os.path.basename(app_path)
    cmake_file = os.path.join(app_path, "CMakeLists.txt")

    if not os.path.exists(cmake_file):
        print(f"[!] ERRO: CMakeLists.txt não encontrado em '{app_path}'.")
        print("    Gere o projeto com o STM32CubeMX primeiro!")
        sys.exit(1)

    print(f"[*] Configurando HIL para o projeto: {project_name}")

    # 1. INJETAR O HIL NO CMAKELISTS.TXT
    # Calcula o caminho relativo da pasta do app até a hil_api
    rel_hil_api = os.path.relpath("hil_api", app_path)
    hil_cmake_path = f"{rel_hil_api}/hil.cmake".replace("\\", "/") # Garante barras de Linux

    with open(cmake_file, "r") as f:
        content = f.read()

    if "INTEGRAÇÃO DO FRAMEWORK HIL" not in content:
        with open(cmake_file, "a") as f:
            f.write("\n\n# " + "="*78 + "\n")
            f.write("# INTEGRAÇÃO DO FRAMEWORK HIL\n")
            f.write("# Automatizado via setup_target.py\n")
            f.write("# " + "="*78 + "\n")
            f.write(f'include("{hil_cmake_path}")\n')
            f.write("inject_hil_framework(${CMAKE_PROJECT_NAME})\n")
        print(f"  [+] CMakeLists.txt atualizado com sucesso.")
    else:
        print(f"  [-] HIL já estava configurado no CMakeLists.txt. Ignorando...")

    # 2. GERAR O PIPELINE DO GITHUB ACTIONS
    yaml_dir = ".github/workflows"
    os.makedirs(yaml_dir, exist_ok=True)
    yaml_file = os.path.join(yaml_dir, f"hil_{project_name}.yml")

    yaml_content = f"""name: HIL Validation - {project_name}

# Dispara este pipeline apenas se arquivos deste projeto ou da ferramenta mudarem
on:
  push:
    paths:
      - '{app_path}/**'
      - 'hil_api/**'
      - 'hil_tool/**'
      
  workflow_dispatch:

jobs:
  build-and-test:
    runs-on: self-hosted
    env:
      FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

    steps:
    - name: Checkout do código
      uses: actions/checkout@v4

    - name: Compilar Firmware ({project_name})
      working-directory: ./{app_path}
      run: |
        rm -rf build/
        cmake --preset Debug -DENABLE_HIL_TESTS=ON
        cmake --build --preset Debug -j$(nproc)

    - name: Executar Testes no Hardware (pyOCD)
      run: |
        if [ ! -d "hil_tool/debug_env" ]; then
          python3 -m venv hil_tool/debug_env
        fi
        source hil_tool/debug_env/bin/activate
        pip install -r hil_tool/requirements.txt
        
        # Inicia a automacao para esta placa especifica
        python3 hil_tool/runner.py --app {app_path}
"""
    with open(yaml_file, "w") as f:
        f.write(yaml_content)
    
    print(f"  [+] Pipeline CI/CD gerado em: {yaml_file}")
    print("\n[OK] Projeto integrado ao HIL! Commit as mudancas para rodar o GitHub Actions.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instalador automatico do HIL para projetos STM32")
    parser.add_argument(
        "--app", 
        type=str, 
        required=True, 
        help="Caminho relativo para a pasta gerada pelo CubeMX (ex: examples/stm32f411_demo)"
    )
    
    args = parser.parse_args()
    setup_hil(args.app)
