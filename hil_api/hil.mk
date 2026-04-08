# hil_framework/hil_api/hil.mk

ifeq ($(ENABLE_HIL), 1)
    $(info >>> [HIL API] MODO HIL ATIVADO: Injeção Definitiva <<<)

    C_SOURCES := $(filter-out %/syscalls.c %/sysmem.c, $(C_SOURCES))
    LIBS := $(filter-out -lnosys, $(LIBS))
    LDFLAGS := $(filter-out -specs=nano.specs, $(LDFLAGS))

    C_DEFS += -DUSE_SEMIHOSTING -DHIL_ACTIVE
    C_INCLUDES += -Ihil_framework/hil_api/inc
    LIBS += -lrdimon
    LDFLAGS += --specs=rdimon.specs

    HIL_OBJ := $(BUILD_DIR)/hil_test.o
    
    # O Makefile original tem a regra: $(BUILD_DIR)/$(TARGET).elf: $(OBJECTS) Makefile
    # Nós avisamos o Make que o .elf também depende do nosso novo arquivo .o
    $(BUILD_DIR)/$(TARGET).elf: $(HIL_OBJ)

$(HIL_OBJ): hil_framework/hil_api/src/hil_test.c Makefile | $(BUILD_DIR)
	@echo "Compilando HIL API: $<"
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/hil_test.lst $< -o $@

    # Injetamos o nosso objeto na lista final que é passada para o Linker (LDFLAGS/CC)
    # injetando o objeto diretamente na string LDFLAGS, para que ele chegue no Linker.
    LDFLAGS += $(HIL_OBJ)

    # ======================================================================
    # ALVO CUSTOMIZADO: flash_test (Execução Local HIL)
    # ======================================================================
    
    # Descobre dinamicamente a pasta onde o hil.mk está e acha a pasta hil_tool
    HIL_API_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
    HIL_TOOL_DIR := $(HIL_API_DIR)../hil_tool

    .PHONY: flash_test
    flash_test: $(BUILD_DIR)/$(TARGET).elf
	@echo ">>> [HIL API] Preparando ambiente e executando testes locais..."
	@if [ ! -d "$(HIL_TOOL_DIR)/debug_env" ]; then \
		echo "Criando ambiente virtual Python..."; \
		python3 -m venv $(HIL_TOOL_DIR)/debug_env; \
	fi
	@bash -c "source $(HIL_TOOL_DIR)/debug_env/bin/activate && \
		  pip install -q -r $(HIL_TOOL_DIR)/requirements.txt && \
		  python3 $(HIL_TOOL_DIR)/runner.py --app ."

endif

