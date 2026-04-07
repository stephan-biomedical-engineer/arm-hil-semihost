#ifndef HIL_TEST_H
#define HIL_TEST_H

#ifdef USE_SEMIHOSTING
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
    
    #define RUN_HIL_TESTS() run_all_tests()

#else
    // =========================================================================
    // MODO PRODUÇÃO 
    // =========================================================================
    
    #define TEST(name) static inline int _ignored_test_##name(void)
    
    static inline void run_all_tests(void) {}
    
    #define RUN_HIL_TESTS() ((void)0)

#endif // USE_SEMIHOSTING

#endif // HIL_TEST_H