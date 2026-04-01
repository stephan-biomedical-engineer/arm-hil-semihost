#include "hil_test.h"

extern test_case_t __tests_start__;
extern test_case_t __tests_end__;

// Declaração obrigatória para o Semihosting no GCC
extern void initialise_monitor_handles(void);

#define HALT_EXECUTION() __asm("BKPT #0")

void run_all_tests(void) 
{
    // Inicializa o roteamento de I/O antes de qualquer printf
    initialise_monitor_handles();

    test_case_t *current_test = &__tests_start__;

    while(current_test < &__tests_end__) 
    {
        int result = current_test->fn();
        printf("TEST:%s:%d\n", current_test->name, result);
        current_test++;
    }

    printf("DONE\n");
    HALT_EXECUTION();
}