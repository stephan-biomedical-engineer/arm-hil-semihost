# hil_framework/hil_api/hil.mk

ifeq ($(ENABLE_HIL), 1)
    $(info >>> [HIL API] MODO HIL ATIVADO: Injeção de dependências <<<)

    C_SOURCES := $(filter-out %/syscalls.c %/sysmem.c, $(C_SOURCES))
    LIBS := $(filter-out -lnosys, $(LIBS))
    LDFLAGS := $(filter-out -specs=nano.specs, $(LDFLAGS))

    C_DEFS += -DUSE_SEMIHOSTING -DHIL_ACTIVE
    C_INCLUDES += -Ihil_framework/hil_api/inc
    
    LIBS += -lrdimon
    LDFLAGS += --specs=rdimon.specs

    HIL_OBJ = $(BUILD_DIR)/hil_test.o
    OBJECTS := $(filter-out $(HIL_OBJ), $(OBJECTS)) $(HIL_OBJ)

    $(BUILD_DIR)/hil_test.o: hil_framework/hil_api/src/hil_test.c Makefile | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/hil_test.lst $< -o $@

endif