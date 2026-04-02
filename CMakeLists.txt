cmake_minimum_required(VERSION 3.22)

#
# This file is generated only once,
# and is not re-generated if converter is called multiple times.
#
# User is free to modify the file as much as necessary
#

# Setup compiler settings
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)


# Define the build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Debug")
endif()

# Set the project name
set(CMAKE_PROJECT_NAME HIL)

# Enable compile command to ease indexing with e.g. clangd
set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

# Core project settings
project(${CMAKE_PROJECT_NAME})
message("Build type: " ${CMAKE_BUILD_TYPE})

# Enable CMake support for ASM and C languages
enable_language(C ASM)

# Create an executable object type
add_executable(${CMAKE_PROJECT_NAME})

# Add STM32CubeMX generated sources
add_subdirectory(cmake/stm32cubemx)

# Link directories setup
target_link_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined library search paths
)

# Add sources to executable
target_sources(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user sources here
    app/src/hil_test.c
)

# Add include paths
target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined include paths
    app/inc
)

list(REMOVE_ITEM CMAKE_C_IMPLICIT_LINK_LIBRARIES ob)

# --- SISTEMA DE OPÇÕES PARA TESTES HIL ---
option(ENABLE_HIL_TESTS "Ativa o framework de testes HIL e Semihosting" OFF)

if(ENABLE_HIL_TESTS)
    message(STATUS ">>> MODO HIL ATIVADO: Vinculando Semihosting (-lrdimon) <<<")
    
    # Liga a macro para desligar o syscalls.c/sysmem.c da ST
    target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE USE_SEMIHOSTING)
    
    # Injeta a biblioteca do Semihosting no Linker
    target_link_options(${CMAKE_PROJECT_NAME} PRIVATE -specs=rdimon.specs)
    
    # Adiciona as bibliotecas base e a do Semihosting
    target_link_libraries(${CMAKE_PROJECT_NAME}
        stm32cubemx
        -lrdimon
        -lc
        -lm
    )
else()
    message(STATUS ">>> MODO PRODUCAO: Semihosting desligado <<<")
    
    # Usa a biblioteca padrão enxuta da ST
    target_link_options(${CMAKE_PROJECT_NAME} PRIVATE -specs=nano.specs)
    
    # Adiciona as bibliotecas base normais
    target_link_libraries(${CMAKE_PROJECT_NAME}
        stm32cubemx
        -lc
        -lm
    )
endif()