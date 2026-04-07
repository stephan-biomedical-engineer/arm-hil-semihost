#include "hil_test.h"

// Declaração obrigatória para o Semihosting no GCC
extern void initialise_monitor_handles(void);

#define HALT_EXECUTION() __asm("BKPT #0")

void run_all_tests(void) 
{
    initialise_monitor_handles();

    // Aponta para a variável mágica gerada pelo GCC
    test_case_t *current_test = &__start_hil_tests;

    // Roda até chegar no fim da seção mágica
    while(current_test < &__stop_hil_tests) 
    {
        int result = current_test->fn();
        
        // Print exato que o regex do runner.py está esperando
        printf("TEST:%s:%d\n", current_test->name, result);
        
        current_test++;
    }

    // Gatilho para o Python parar o loop de timeout
    printf("DONE\n");
    
    HALT_EXECUTION();
}