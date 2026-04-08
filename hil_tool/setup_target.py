import os
import sys
import argparse

def setup_hil(app_path, is_internal=False):
    absolute_path = os.path.abspath(app_path)
    project_name = os.path.basename(absolute_path)
    if not project_name or project_name == ".":
        project_name = "stm32_project"

    cmake_file = os.path.join(app_path, "CMakeLists.txt")
    makefile = os.path.join(app_path, "Makefile")
    
    build_system = None
    if os.path.exists(cmake_file):
        build_system = "cmake"
    elif os.path.exists(makefile):
        build_system = "makefile"
    else:
        print(f"[!] ERRO: Nenhum CMakeLists.txt ou Makefile encontrado em '{app_path}'.")
        sys.exit(1)

    print(f"[*] Projeto detectado: {project_name} ({build_system.upper()})")

    # ==========================================
    # LÓGICA DE CAMINHOS (INTERNO VS EXTERNO)
    # ==========================================
    if is_internal:
        # Se for interno, calculamos o caminho de volta para a raiz do repo
        hil_lib_path_yaml = "."
        trigger_paths = f"      - 'hil_api/**'\n      - 'hil_tool/**'"
        # Calcula como chegar na hil_api saindo de dentro do app_path
        hil_cmake_path = os.path.relpath("hil_api/hil.cmake", start=app_path)
        hil_mk_path = os.path.relpath("hil_api/hil.mk", start=app_path)
    else:
        # Se for usuário final, assume a pasta do submódulo
        hil_lib_path_yaml = "hil_framework"
        trigger_paths = f"      - 'hil_framework/**'"
        hil_cmake_path = "hil_framework/hil_api/hil.cmake"
        hil_mk_path = "hil_framework/hil_api/hil.mk"

    # ==========================================
    # INJEÇÃO NO ARQUIVO DE BUILD
    # ==========================================
    if build_system == "cmake":
        with open(cmake_file, "r") as f:
            content = f.read()
        if "INTEGRAÇÃO DO FRAMEWORK HIL" not in content:
            with open(cmake_file, "a") as f:
                f.write(f"\n\n# {'='*70}\n# INTEGRAÇÃO DO FRAMEWORK HIL\n# {'='*70}\n")
                # No CMake, precisamos converter barras invertidas do Windows para barras normais
                f.write(f'include("{hil_cmake_path.replace(os.sep, "/")}")\n')
                f.write("inject_hil_framework(${CMAKE_PROJECT_NAME})\n")
            print(f"  [+] CMakeLists.txt atualizado.")
        else:
            print(f"  [-] HIL já estava configurado no CMake. Ignorando...")
            
    elif build_system == "makefile":
        with open(makefile, "r") as f:
            content = f.read()            
        if "INTEGRAÇÃO DO FRAMEWORK HIL" not in content:
            with open(makefile, "a") as f:
                f.write(f"\n\n# {'='*70}\n# INTEGRAÇÃO DO FRAMEWORK HIL\n")
                f.write(f"-include {hil_mk_path.replace(os.sep, '/')}\n")
            print(f"  [+] Makefile atualizado.")
        else:
            print(f"  [-] HIL já estava configurado no Makefile. Ignorando...")

    # ==========================================
    # GERAÇÃO DO YAML DO GITHUB ACTIONS
    # ==========================================
    yaml_dir = ".github/workflows"
    os.makedirs(yaml_dir, exist_ok=True)
    yaml_file = os.path.join(yaml_dir, f"hil_{project_name}.yml")

    if build_system == "cmake":
        build_commands = f"""rm -rf build/
        cmake --preset Debug -DENABLE_HIL_TESTS=ON
        cmake --build --preset Debug -j$(nproc)"""
    else:
        build_commands = f"make clean\n        make ENABLE_HIL=1 -j$(nproc)"

    yaml_content = f"""name: HIL Validation - {project_name}

on:
  workflow_dispatch:

jobs:
  build-and-test:
    runs-on: self-hosted
    env:
      FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

    steps:
    - name: Checkout do código
      uses: actions/checkout@v4
      with:
        submodules: recursive

    - name: Compilar Firmware ({build_system.upper()})
      working-directory: ./{app_path}
      run: |
        {build_commands}

    - name: Executar Testes no Hardware (pyOCD)
      run: |
        HIL_LIB="{hil_lib_path_yaml}"
        if [ ! -d "$HIL_LIB/hil_tool/debug_env" ]; then
          python3 -m venv $HIL_LIB/hil_tool/debug_env
        fi
        source $HIL_LIB/hil_tool/debug_env/bin/activate
        pip install -q -r $HIL_LIB/hil_tool/requirements.txt
        python3 $HIL_LIB/hil_tool/runner.py --app {app_path}
"""
    with open(yaml_file, "w") as f:
        f.write(yaml_content)
    
    print(f"  [+] Pipeline CI/CD gerado: {yaml_file}")
    print(f"\n[OK] Projeto {project_name} pronto para HIL!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instalador automatico do HIL para projetos STM32")
    parser.add_argument("--app", type=str, required=True, help="Caminho relativo para a pasta do projeto")
    parser.add_argument("--internal", action="store_true", help="Usa caminhos relativos para exemplos dentro do proprio repositorio do framework")
    
    args = parser.parse_args()
    setup_hil(args.app, args.internal)