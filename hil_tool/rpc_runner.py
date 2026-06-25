import os
import sys
import glob
import json
import subprocess
from pyocd.core.helpers import ConnectHelper

# Assegura que o módulo raiz pode ser importado
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hil_tool.hil_rpc import call_target_function

def load_tests(filepath):
    try:
        if filepath.endswith('.yaml') or filepath.endswith('.yml'):
            import yaml
            with open(filepath, 'r') as f:
                return yaml.safe_load(f).get("tests", [])
        else:
            with open(filepath, 'r') as f:
                return json.load(f).get("tests", [])
    except Exception as e:
        print(f"[!] ERRO ao ler arquivo de testes '{filepath}': {e}")
        sys.exit(1)

def get_symbol_address(elf_path, symbol_name):
    """Extrai o endereço de uma função usando arm-none-eabi-nm."""
    try:
        result = subprocess.run(
            ["arm-none-eabi-nm", elf_path], 
            capture_output=True, text=True, check=True
        )
        for line in result.stdout.splitlines():
            if symbol_name in line:
                addr_str = line.split()[0]
                return int(addr_str, 16)
    except Exception as e:
        print(f"[!] Erro ao extrair símbolo com nm: {e}")
    return None

def run_rpc_tests(app_path, tests_file):
    print("="*50)
    print("    Execução de Testes RPC - HIL Framework")
    print("="*50 + "\n")

    tests_path = os.path.join(app_path, tests_file)
    if not os.path.exists(tests_path):
        print(f"[!] ERRO: Arquivo de testes não encontrado: {tests_path}")
        sys.exit(1)

    tests = load_tests(tests_path)
    if not tests:
        print(f"[!] Nenhum teste RPC definido em {tests_file}.")
        sys.exit(0)

    print(f"[*] Encontrados {len(tests)} testes RPC.")

    # Acha o ELF
    elf_files = glob.glob(os.path.join(app_path, "build", "**", "*.elf"), recursive=True)
    elf_files = [f for f in elf_files if "CMakeFiles" not in f]
    
    if not elf_files:
        print(f"[!] ERRO: Nenhum arquivo .elf encontrado em '{app_path}/build/'. Compile o projeto primeiro.")
        sys.exit(1)
        
    elf_file = elf_files[0]
    print(f"[*] Usando binário: {elf_file}")

    print("[*] Conectando à placa via pyOCD...")
    session = ConnectHelper.session_with_chosen_probe(blocking=False)
    if session is None:
        print("[!] ERRO: Nenhuma placa detectada.")
        sys.exit(1)

    results = {}
    
    with session:
        target = session.board.target

        for test in tests:
            name = test.get("name", "Unnamed Test")
            func_name = test.get("function")
            args = test.get("args", [])
            expected = test.get("expected")

            print(f"\n>>> Executando: {name}")
            print(f"    Função: {func_name}{args} -> Esperado: {expected}")
            
            addr = get_symbol_address(elf_file, func_name)
            if not addr:
                print(f"    [!] Símbolo '{func_name}' não encontrado no ELF. Ignorando...")
                results[name] = False
                continue
                
            try:
                ret = call_target_function(target, addr, args=args)
                if ret == expected:
                    print(f"    [ PASS ] Retornou: {ret}")
                    results[name] = True
                else:
                    print(f"    [ FAIL ] Retornou {ret}, mas esperava {expected}.")
                    results[name] = False
            except Exception as e:
                print(f"    [ FAIL ] Erro na injeção: {e}")
                results[name] = False

    print("\n" + "="*50)
    print("RESUMO DOS TESTES RPC")
    print("="*50)
    
    failed_tests = [k for k, v in results.items() if not v]
    
    for name, passed in results.items():
        print(f"[{' PASS ' if passed else ' FAIL '}] {name}")
        
    if failed_tests:
        print(f"\n[ RESULTADO ] FALHA em {len(failed_tests)} teste(s) RPC.")
        sys.exit(1)
    else:
        print(f"\n[ RESULTADO ] SUCESSO. Todos os {len(results)} testes RPC passaram.")
        sys.exit(0)
