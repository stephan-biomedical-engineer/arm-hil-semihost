# hil_api/hil.cmake

# A opção global que o GitHub Actions vai acionar
option(ENABLE_HIL_TESTS "Ativa o framework de testes HIL e Semihosting" OFF)

# Função para injetar a ferramenta em qualquer firmware
function(inject_hil_framework TARGET_NAME)
    target_include_directories(${TARGET_NAME} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/inc)
    if(ENABLE_HIL_TESTS)
        message(STATUS ">>> [HIL API] MODO HIL ATIVADO: Injetando Semihosting no ${TARGET_NAME} <<<")

        get_target_property(APP_SOURCES ${TARGET_NAME} SOURCES)
        list(FILTER APP_SOURCES EXCLUDE REGEX "syscalls\\.c|sysmem\\.c")
        set_target_properties(${TARGET_NAME} PROPERTIES SOURCES "${APP_SOURCES}")
        
        target_sources(${TARGET_NAME} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/src/hil_test.c)
        
        target_compile_definitions(${TARGET_NAME} PRIVATE USE_SEMIHOSTING)
        target_link_options(${TARGET_NAME} PRIVATE -specs=rdimon.specs)
        target_link_libraries(${TARGET_NAME} -lrdimon -lc -lm)
    else()
        message(STATUS ">>> [HIL API] MODO PRODUCAO: Semihosting desligado no ${TARGET_NAME} <<<")
        
        target_link_options(${TARGET_NAME} PRIVATE -specs=nano.specs)
        target_link_libraries(${TARGET_NAME} -lc -lm)
    endif()
endfunction()
