ifeq ($(ENABLE_HIL), 1)
    $(info >>> [HIL API] MODO HIL ATIVADO: Injetando Semihosting <<<)

    # Remove syscalls.o e sysmem.o da lista de objetos
    # O Makefile da ST usa $(C_SOURCES:.c=.o) para gerar $(OBJECTS).
    C_SOURCES := $(filter-out %/syscalls.c %/sysmem.c, $(C_SOURCES))

    C_SOURCES += hil_framework/hil_api/src/hil_test.c
    C_INCLUDES += -Ihil_framework/hil_api/inc

    C_DEFS += -DUSE_SEMIHOSTING -DHIL_ACTIVE
    LIBS += -lrdimon
    LDFLAGS += --specs=rdimon.specs
endif
