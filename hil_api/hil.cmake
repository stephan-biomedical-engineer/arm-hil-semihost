# hil_api/hil.cmake

# A opção global que o GitHub Actions vai acionar
option(ENABLE_HIL_TESTS "Ativa o framework de testes HIL e Semihosting" OFF)

# Função para injetar a ferramenta em qualquer firmware
function(inject_hil_framework TARGET_NAME)
    if(ENABLE_HIL_TESTS)
        message(STATUS ">>> [HIL API] MODO HIL ATIVADO: Injetando Semihosting no ${TARGET_NAME} <<<")
        
        # O CMAKE_CURRENT_FUNCTION_LIST_DIR garante que os caminhos serão sempre relativos 
        # a este arquivo hil.cmake, não importando de onde o exemplo seja chamado!
        target_sources(${TARGET_NAME} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/src/hil_test.c)
        target_include_directories(${TARGET_NAME} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/inc)
        
        # Injeta as regras do Semihosting
        target_compile_definitions(${TARGET_NAME} PRIVATE USE_SEMIHOSTING)
        target_link_options(${TARGET_NAME} PRIVATE -specs=rdimon.specs)
        target_link_libraries(${TARGET_NAME} -lrdimon -lc -lm)
    else()
        message(STATUS ">>> [HIL API] MODO PRODUCAO: Semihosting desligado no ${TARGET_NAME} <<<")
        
        target_link_options(${TARGET_NAME} PRIVATE -specs=nano.specs)
        target_link_libraries(${TARGET_NAME} -lc -lm)
    endif()
endfunction()
