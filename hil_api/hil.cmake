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

        # ======================================================================
        # ALVO CUSTOMIZADO: flash_test (Execução Local HIL)
        # ======================================================================
        set(HIL_TOOL_DIR "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../hil_tool")

        # Em vez de um if() complexo em bash, usamos o comando cmake -E
        # que é multiplataforma e não sofre com problemas de aspas.
        add_custom_target(flash_test
            # Passo 1: Cria o VENV (só cria se não existir)
            COMMAND python3 -m venv ${HIL_TOOL_DIR}/debug_env
            # Passo 2: Chama o pip DE DENTRO do venv para instalar (sem precisar do 'source')
            COMMAND ${HIL_TOOL_DIR}/debug_env/bin/python3 -m pip install -q -r ${HIL_TOOL_DIR}/requirements.txt
            # Passo 3: Chama o runner DE DENTRO do venv
            COMMAND ${HIL_TOOL_DIR}/debug_env/bin/python3 ${HIL_TOOL_DIR}/runner.py --app ${CMAKE_SOURCE_DIR}
            
            DEPENDS ${TARGET_NAME}
            WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
            COMMENT ">>> [HIL API] Preparando ambiente e executando testes locais via pyOCD..."
        )

    else()
        message(STATUS ">>> [HIL API] MODO PRODUCAO: Semihosting desligado no ${TARGET_NAME} <<<")
        
        target_link_options(${TARGET_NAME} PRIVATE -specs=nano.specs)
        target_link_libraries(${TARGET_NAME} -lc -lm)
    endif()
endfunction()
