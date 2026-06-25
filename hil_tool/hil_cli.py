import os
import sys
import subprocess
import argparse
import shutil
from setup_target import setup_hil

def run_subprocess(cmd, cwd=".", shell=False):
    """Executa um subprocesso e repassa o retorno."""
    print(f"[*] Executando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        subprocess.run(cmd, cwd=cwd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] ERRO: Comando falhou com código {e.returncode}.")
        sys.exit(e.returncode)

def do_install(app_path):
    print("="*50)
    print("    Instalador Automático: ARM HIL Framework")
    print("="*50 + "\n")
    
    app_abs = os.path.abspath(app_path)
    if not os.path.exists(os.path.join(app_abs, "CMakeLists.txt")) and not os.path.exists(os.path.join(app_abs, "Makefile")):
        print("[!] ERRO: Nenhum sistema de build (CMake ou Makefile) detectado!")
        print("    Gere o projeto no STM32CubeMX primeiro.")
        sys.exit(1)

    # 1. Gerenciamento de Git/Submódulo
    if not os.path.exists(os.path.join(app_abs, ".git")):
        print("[*] Inicializando repositório Git...")
        run_subprocess(["git", "init"], cwd=app_abs)
    
    print("[*] Configurando submódulo em hil_framework...")
    hil_framework_dir = os.path.join(app_abs, "hil_framework")
    if not os.path.exists(hil_framework_dir):
        run_subprocess(["git", "submodule", "add", "https://github.com/stephan-biomedical-engineer/arm-hil-semihost.git", "hil_framework"], cwd=app_abs)
    else:
        print("    Atualizando submódulo existente...")
        run_subprocess(["git", "submodule", "update", "--init", "--recursive"], cwd=app_abs)

    # 2. Execução do Integrador Python
    print("\n[*] Acionando o integrador...")
    setup_hil(app_path, is_internal=False)
    print("\n[OK] Instalação concluída com sucesso!")

def do_run(app_path):
    print("="*50)
    print("    ARM HIL Framework - Teste Local Automatizado")
    print("="*50 + "\n")
    
    app_abs = os.path.abspath(app_path)
    print(f"[*] Diretório do projeto: {app_abs}")
    
    import multiprocessing
    nproc = str(multiprocessing.cpu_count())

    if os.path.exists(os.path.join(app_abs, "CMakeLists.txt")):
        print("[*] Sistema de build detectado: CMake\n")
        
        print(">>> Passo 1/3: Limpando build antigo...")
        build_dir = os.path.join(app_abs, "build")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
            
        print("\n>>> Passo 2/3: Configurando CMake para testes HIL...")
        presets_file = os.path.join(app_abs, "CMakePresets.json")
        has_debug_preset = False
        if os.path.exists(presets_file):
            with open(presets_file, "r") as f:
                if "Debug" in f.read():
                    has_debug_preset = True
        
        if has_debug_preset:
            run_subprocess(["cmake", "--preset", "Debug", "-DENABLE_HIL_TESTS=ON"], cwd=app_abs)
            build_cmd = ["cmake", "--build", "--preset", "Debug", "--target", "flash_test", "-j", nproc]
        else:
            run_subprocess(["cmake", "-B", "build", "-DCMAKE_BUILD_TYPE=Debug", "-DENABLE_HIL_TESTS=ON"], cwd=app_abs)
            build_cmd = ["cmake", "--build", "build", "--target", "flash_test", "-j", nproc]
            
        print("\n>>> Passo 3/3: Compilando e executando testes...")
        run_subprocess(build_cmd, cwd=app_abs)

    elif os.path.exists(os.path.join(app_abs, "Makefile")):
        print("[*] Sistema de build detectado: Makefile\n")
        
        print(">>> Passo 1/2: Limpando build antigo...")
        run_subprocess(["make", "clean"], cwd=app_abs)
        
        print("\n>>> Passo 2/2: Compilando e executando testes...")
        run_subprocess(["make", "ENABLE_HIL=1", "flash_test", "-j", nproc], cwd=app_abs)
        
    else:
        print("[!] ERRO: Nenhum sistema de build (CMake ou Makefile) detectado na pasta.")
        print("    Certifique-se de estar na raiz do projeto STM32.")
        sys.exit(1)

    print("\n=================================================")
    print("    Processo de Teste Local Concluído!           ")
    print("=================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARM HIL Framework CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Instala e configura o framework HIL no projeto")
    install_parser.add_argument("--app", type=str, default=".", help="Caminho relativo para a pasta do projeto")

    run_parser = subparsers.add_parser("run", help="Compila o projeto e executa os testes HIL na placa")
    run_parser.add_argument("--app", type=str, default=".", help="Caminho relativo para a pasta do projeto")

    rpc_parser = subparsers.add_parser("rpc", help="Executa testes de Injeção de Função (RPC) baseados em JSON")
    rpc_parser.add_argument("--app", type=str, default=".", help="Caminho relativo para a pasta do projeto")
    rpc_parser.add_argument("--tests", type=str, default="rpc_tests.json", help="Arquivo de testes RPC (Padrão: rpc_tests.json)")

    args = parser.parse_args()

    if args.command == "install":
        do_install(args.app)
    elif args.command == "run":
        do_run(args.app)
    elif args.command == "rpc":
        from rpc_runner import run_rpc_tests
        run_rpc_tests(args.app, args.tests)
