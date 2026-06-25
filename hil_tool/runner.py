import os
import sys
import time
import re
import argparse
import glob
import json
import subprocess
from pyocd.core.helpers import ConnectHelper
from pyocd.flash.file_programmer import FileProgrammer
from pyocd.core.target import Target
from pyocd.debug import semihost

# Classe para interceptar os dados lendo direto da RAM da placa
class HILConsole:
    def __init__(self, context):
        self.captured_output = ""
        self.context = context

    def write(self, fd, data_ptr, length):
        # 1. Lê os bytes diretamente do endereço de RAM informado pelo Cortex-M33
        data = self.context.read_memory_block8(data_ptr, length)
        
        # 2. Converte o array de bytes para texto
        text = bytes(data).decode('utf-8', 'ignore')
        self.captured_output += text
        
        # 3. Imprime no terminal em tempo real
        sys.stdout.write(text)
        sys.stdout.flush()
        
        # 4. Retorna 0 para o microcontrolador (sucesso na escrita)
        return 0 

    def read(self, fd, data_ptr, length):
        return -1 # Não usaremos envio de teclado para a placa

    def readc(self):
        return -1

def run_hil_tests(app_path, flash_backend="pyocd", probe=None, auto_dump=True, timeout=5.0, stm32_cli_path="STM32_Programmer_CLI"):

    # Ativa a busca recursiva adicionando "**" e recursive=True
    elf_files = glob.glob(os.path.join(app_path, "build", "**", "*.elf"), recursive=True)

    # (Opcional) Filtra lixos de compilação interna do CMake
    elf_files = [f for f in elf_files if "CMakeFiles" not in f]
    
    if not elf_files:
        print(f"[!] ERRO: Nenhum arquivo .elf encontrado em '{app_path}/build/'")
        print("    Certifique-se de compilar o projeto antes de rodar o runner.")
        sys.exit(1)

    if len(elf_files) > 1:
        print(f"[!] AVISO: Múltiplos arquivos .elf encontrados. Usando: {elf_files[0]}")
        
    elf_file = elf_files[0]

    options = {
        "enable_semihosting": False, 
        "semihost_console_type": "console",
        "semihost_use_syscalls": False
    }
    
    session = ConnectHelper.session_with_chosen_probe(options=options, blocking=False)
    if session is None:
        sys.exit(1)

    with session:
        target = session.board.target

        print(f"[*] Gravando firmware: {elf_file} (Backend: {flash_backend})")
        if flash_backend == "pyocd":
            programmer = FileProgrammer(session)
            programmer.program(elf_file)
        elif flash_backend == "stm32":
            cmd = [stm32_cli_path, "-c", "port=SWD"]
            if probe: cmd.extend([f"sn={probe}"])
            cmd.extend(["-w", elf_file, "-v", "-rst"])
            subprocess.run(cmd, check=True)
            time.sleep(1) # Aguarda reset
        elif flash_backend == "jlink":
            print("[!] Suporte a J-Link via CLI pendente (fallback para pyOCD).")
            programmer = FileProgrammer(session)
            programmer.program(elf_file)

        print("[*] Iniciando infraestrutura de testes...\n")
        
        target_context = target.get_target_context()
        
        hil_console = HILConsole(target_context)
        io_handler = semihost.InternalSemihostIOHandler()
        
        agent = semihost.SemihostAgent(
            target_context,
            io_handler=io_handler,
            console=hil_console 
        )

        target.reset_and_halt()
        target.resume()

        timeout_counter = 0

        while True:
            if target.get_state() == Target.State.HALTED:
                
                was_semihost = agent.check_and_handle_semihost_request()
                
                if was_semihost:
                    target.resume()
                    timeout_counter = 0
                else:
                    break # HALT_EXECUTION() (BKPT 0)
                    
            if "DONE" in hil_console.captured_output:
                break

            if auto_dump:
                current_results = parse_results(hil_console.captured_output)
                if any(status != 0 for status in current_results.values()):
                    print("\n[!] Falha detectada durante a execução! Gerando dump post-mortem...")
                    target.halt()
                    print("\n--- CORE REGISTERS ---")
                    for reg in ['r0', 'r1', 'r2', 'r3', 'r12', 'sp', 'lr', 'pc', 'xpsr']:
                        try:
                            val = target.read_core_register(reg)
                            print(f"{reg.upper()}: 0x{val:08X}")
                        except:
                            pass
                    print("----------------------\n")
                    break

            time.sleep(0.01)
            timeout_counter += 1
            max_iters = int(timeout * 100)
            if timeout_counter > max_iters: 
                print(f"\n[!] Timeout: Placa parou de responder após {timeout} segundos.")
                break

        target.halt()
        
        # Retorna o texto bruto capturado para o parser
        return parse_results(hil_console.captured_output)

def parse_results(output):
    results = {}
    matches = re.findall(r"TEST:(.*?):(\d+)", output)
    for name, status in matches:
        results[name] = int(status)
    return results

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Runner HIL para STM32 via pyOCD")
    parser.add_argument(
        "--app", 
        type=str, 
        required=True, 
        help="Caminho relativo para a pasta do projeto (ex: examples/stm32u5_demo)"
    )
    parser.add_argument("--flash-backend", type=str, default="pyocd", choices=["pyocd", "stm32", "jlink"])
    parser.add_argument("--probe", type=str, default=None)
    parser.add_argument("--report-xml", type=str, default=None)
    parser.add_argument("--report-json", type=str, default=None)
    parser.add_argument("--no-auto-dump", action="store_true")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout em segundos (padrão: 5.0)")
    parser.add_argument("--stm32-cli-path", type=str, default="STM32_Programmer_CLI", help="Caminho para o executável do STM32CubeProgrammer")

    args = parser.parse_args()

    from config import load_config, override_args

    # Carrega configurações do arquivo (YAML ou JSON) e sobrescreve argumentos não fornecidos na CLI
    cfg = load_config(args.app)
    args = override_args(args, cfg, sys.argv)

    results = run_hil_tests(
        args.app, 
        flash_backend=args.flash_backend, 
        probe=args.probe, 
        auto_dump=not args.no_auto_dump,
        timeout=args.timeout,
        stm32_cli_path=args.stm32_cli_path
    )

    if args.report_xml:
        with open(args.report_xml, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<testsuites>\n')
            f.write(f'  <testsuite name="HIL Tests" tests="{len(results)}">\n')
            for name, status in results.items():
                f.write(f'    <testcase classname="hil" name="{name}">\n')
                if status != 0:
                    f.write(f'      <failure message="Test failed with code {status}" />\n')
                f.write('    </testcase>\n')
            f.write('  </testsuite>\n</testsuites>\n')
            print(f"[*] Relatório XML salvo em: {args.report_xml}")

    if args.report_json:
        with open(args.report_json, 'w') as f:
            json.dump(results, f, indent=4)
            print(f"[*] Relatório JSON salvo em: {args.report_json}")

    print("\n" + "="*30)
    print("RESUMO DOS TESTES")
    print("="*30)

    failed_tests = []
    for test_name, status in results.items():
        if status == 0:
            print(f"[ PASS ] {test_name}")
        else:
            print(f"[ FAIL ] {test_name}")
            failed_tests.append(test_name)

    if failed_tests:
        print(f"\n[ RESULTADO ] FALHA em {len(failed_tests)} teste(s).")
        sys.exit(1)
    else:
        print(f"\n[ RESULTADO ] SUCESSO. Todos os {len(results)} testes passaram.")
        sys.exit(0)
