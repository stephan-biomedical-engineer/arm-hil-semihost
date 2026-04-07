/* hil_api/hil_linker.ld */
/* Este script anexa a infraestrutura de testes ao linker principal sem modifica-lo */

SECTIONS
{
  .tests :
  {
    . = ALIGN(8);
    PROVIDE_HIDDEN(__tests_start__ = .);
    KEEP(*(.tests))
    PROVIDE_HIDDEN(__tests_end__ = .);
    . = ALIGN(8);
  }
} INSERT AFTER .text;