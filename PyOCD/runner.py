import sys
import time
import re
from pyocd.core.helpers import ConnectHelper
from pyocd.flash.file_programmer import FileProgrammer
from pyocd.core.target import Target
from pyocd.debug import semihost

ELF_FILE = "build/Debug/HIL.elf"

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

def run_hil_tests():
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

        print("[*] Gravando firmware...")
        programmer = FileProgrammer(session)
        programmer.program(ELF_FILE)

        print("[*] Iniciando infraestrutura de testes...\n")
        
        target_context = target.get_target_context()
        
        # Injetamos o nosso terminal customizado no agente do pyOCD
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
                    break # Foi o nosso HALT_EXECUTION() (BKPT 0)
                    
            # Analisa o que o nosso terminal interceptou
            if "DONE" in hil_console.captured_output:
                break

            time.sleep(0.01)
            timeout_counter += 1
            if timeout_counter > 500: 
                print("\n[!] Timeout: Placa parou de responder.")
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
    results = run_hil_tests()

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