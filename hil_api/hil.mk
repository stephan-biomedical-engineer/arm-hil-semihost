# hil_framework/hil_api/hil.mk

ifeq ($(ENABLE_HIL), 1)
    $(info >>> [HIL API] MODO HIL ATIVADO: Ajustando variáveis de build <<<)

    C_SOURCES := $(filter-out %/syscalls.c %/sysmem.c, $(C_SOURCES))

    C_SOURCES += hil_framework/hil_api/src/hil_test.c
    C_INCLUDES += -Ihil_framework/hil_api/inc
    
    OBJECTS += $(BUILD_DIR)/hil_test.o
    
    vpath hil_test.c hil_framework/hil_api/src

    C_DEFS += -DUSE_SEMIHOSTING -DHIL_ACTIVE

    LIBS := $(filter-out -lnosys, $(LIBS))
    LIBS += -lrdimon

    LDFLAGS := $(filter-out --specs=nano.specs, $(LDFLAGS))
    LDFLAGS += --specs=rdimon.specs
endif