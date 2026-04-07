/* hil_api/inc/hil_test.h */
#ifndef HIL_TEST_H
#define HIL_TEST_H

#ifdef HIL_ACTIVE
    // =========================================================================
    // MODO TESTE (HIL ATIVADO)
    // =========================================================================
    #include <stdio.h>

    typedef int (*test_fn_t)(void);

    typedef struct 
    {
        const char *name;
        test_fn_t fn;
    } test_case_t;

    #define TEST(name) \
        int name(void); \
        __attribute__((section("hil_tests"), used)) \
        const test_case_t _test_##name = {#name, name}; \
        int name(void)

    extern test_case_t __start_hil_tests;
    extern test_case_t __stop_hil_tests;

    void run_all_tests(void);
    
    // Macro que o usuário chama no main.c
    #define RUN_HIL_TESTS() run_all_tests()

#else
    // =========================================================================
    // MODO PRODUÇÃO 
    // =========================================================================
    
    // Transforma o código do teste em uma função fantasma que o Linker descarta
    #define TEST(name) static inline void _ignored_test_##name(void)
    
    // Apaga a chamada do main.c (substitui por nada)
    #define RUN_HIL_TESTS() ((void)0)

#endif // HIL_ACTIVE

#endif // HIL_TEST_H