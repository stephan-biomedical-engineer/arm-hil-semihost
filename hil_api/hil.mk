# hil_framework/hil_api/hil.mk

ifeq ($(ENABLE_HIL), 1)
    $(info >>> [HIL API] MODO HIL ATIVADO: Sincronizando dependências <<<)

    C_SOURCES := $(filter-out %/syscalls.c %/sysmem.c, $(C_SOURCES))
    LIBS := $(filter-out -lnosys, $(LIBS))
    LDFLAGS := $(filter-out -specs=nano.specs, $(LDFLAGS))

    C_SOURCES += hil_framework/hil_api/src/hil_test.c
    C_INCLUDES += -Ihil_framework/hil_api/inc

    vpath hil_test.c hil_framework/hil_api/src

    C_DEFS += -DUSE_SEMIHOSTING -DHIL_ACTIVE
    LIBS += -lrdimon
    LDFLAGS += --specs=rdimon.specs
endif