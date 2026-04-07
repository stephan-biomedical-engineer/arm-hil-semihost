#ifndef HIL_TEST_H
#define HIL_TEST_H

#include <stdio.h>

// Assinatura de um teste: retorna 0 para sucesso, qualquer outra coisa para falha
typedef int (*test_fn_t)(void);

// Estrutura que será gravada na seção especial da Flash
typedef struct 
{
    const char *name;
    test_fn_t fn;
} test_case_t;

// Macro para registrar o teste na seção ".tests"
#define TEST(name) \
    int name(void); \
    __attribute__((section(".tests"), used)) \
    const test_case_t _test_##name = {#name, name}; \
    int name(void)

void run_all_tests(void);

#endif // HIL_TEST_H
