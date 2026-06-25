import time
from pyocd.core.target import Target

def call_target_function(target, symbol_address, args=[]):
    """
    Executa uma função em runtime no microcontrolador via pyOCD.
    
    Atenção: Esta implementação usa manipulação direta de registradores (AAPCS).
    Suporta no máximo 4 argumentos inteiros (passados em r0-r3).
    
    :param target: Objeto Target do pyOCD.
    :param symbol_address: Endereço da função C na memória flash/ram.
    :param args: Lista de argumentos inteiros.
    :return: Valor de retorno da função (lido do r0).
    """
    # 1. Pausa a CPU
    target.halt()
    
    # 2. Salva o contexto dos registradores
    registers_to_save = ['r0', 'r1', 'r2', 'r3', 'sp', 'lr', 'pc', 'xpsr']
    original_regs = {reg: target.read_core_register(reg) for reg in registers_to_save}
    
    try:
        # 3. Carrega os argumentos nos registradores R0-R3 (AAPCS)
        for _reg in range(min(len(args), 4)):
            target.write_core_register(f'r{_reg}', args[_reg])
            
        # 4. Define o LR para um endereço de parada seguro
        # Em Cortex-M, podemos usar um endereço genérico de RAM onde gravamos
        # temporariamente a instrução BKPT (0xBE00)
        RAM_BKPT_ADDR = 0x20000000  # Endereço genérico de RAM
        
        # Lê os 2 bytes originais para restaurar depois
        original_mem = target.read_memory_block8(RAM_BKPT_ADDR, 2)
        
        # Escreve a instrução BKPT 0 (0xBE00)
        target.write_memory16(RAM_BKPT_ADDR, 0xBE00) 
        
        # Define o LR para apontar para o nosso BKPT temporário (com bit 0 em 1 para modo Thumb)
        target.write_core_register('lr', RAM_BKPT_ADDR | 1)
        
        # 5. Define o PC para a função que queremos chamar
        target.write_core_register('pc', symbol_address | 1)
        
        # 6. Executa a função e aguarda parar no BKPT
        target.resume()
        
        # Aguarda a função terminar (máximo de 1 segundo)
        timeout = time.time() + 1.0
        while target.get_state() != Target.State.HALTED:
            if time.time() > timeout:
                raise TimeoutError("A função no target demorou demais para responder.")
            time.sleep(0.005)
            
        # 7. Lê o valor de retorno em R0
        return_value = target.read_core_register('r0')
        
        # Restaura a memória original do BKPT temporário
        target.write_memory_block8(RAM_BKPT_ADDR, original_mem)
        
        return return_value
        
    finally:
        # 8. Restaura o estado da CPU exatamente como estava antes
        for reg, value in original_regs.items():
            target.write_core_register(reg, value)
        target.resume()
