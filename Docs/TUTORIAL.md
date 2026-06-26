# Tutorial da API HIL (Hardware-in-the-Loop)

O framework `arm-hil-semihost` fornece uma API simples para criar e executar testes diretamente no hardware físico (STM32/ARM Cortex-M), automatizando o feedback para o host (computador) via Semihosting.

Neste tutorial, você aprenderá a:
1. Escrever testes em C rodando no microcontrolador.
2. Configurar o projeto usando YAML/JSON.
3. Rodar os testes localmente com a CLI Python.
4. Fazer debug com a injeção avançada de funções.

---

## 1. Escrevendo Testes no Firmware (Lado C)

A API do framework expõe uma macro muito simples chamada `TEST()`. Para começar, crie um arquivo no seu projeto, por exemplo `src/meus_testes.c`.

### 1.1 Incluindo o Cabeçalho
```c
#include "hil_test.h"
#include "meu_sensor.h"
```

### 1.2 Definindo os Testes
Use a macro `TEST(nome_do_teste)` para definir blocos de teste. O teste deve retornar `0` em caso de sucesso, ou um número maior que `0` em caso de falha.

```c
// Exemplo de Teste de Matemática Básica
TEST(teste_soma_basica) {
    int resultado = 2 + 2;
    if (resultado != 4) return 1; // Falha
    
    return 0; // Sucesso
}

// Exemplo de Teste Unitário Acoplado ao Hardware (HIL)
TEST(teste_leitura_sensor) {
    int valor_adc = ler_sensor_analogico();
    
    if (valor_adc < 100 || valor_adc > 4000) {
        return 1; // Leitura fora dos limites da realidade física
    }
    
    return 0; // Leitura válida
}
```

### 1.3 Chamando o Motor de Testes
Em algum lugar da sua `main.c` (ou em uma thread separada do RTOS), você precisa acionar a execução de todos os testes compilados.

```c
#include "hil_test.h"

int main(void) {
    HAL_Init();
    SystemClock_Config();
    
    // Configura periféricos...
    
    // Executa a bateria de testes HIL e manda os resultados pro Host!
    RUN_HIL_TESTS();
    
    while (1) {
        // Seu código normal
    }
}
```
*Nota: Se o projeto não for compilado no modo HIL, a macro `RUN_HIL_TESTS()` será silenciosamente ignorada e descartada para não roubar processamento em Produção.*

---

## 2. Configurando o Projeto (Lado Host)

Na raiz do seu projeto (junto do seu `Makefile` ou `CMakeLists.txt`), crie um arquivo chamado `hil.yaml` para configurar as ferramentas da máquina de testes.

```yaml
# hil.yaml
flash_backend: pyocd       # Utiliza o PyOCD nativo para gravação
timeout: 300.0             # Espera até 5 minutos pelos resultados demorados
auto_dump: true            # Se um teste falhar, cospe os registradores da CPU!
report_xml: "testes.xml"   # Gera um log JUnit no final
```

---

## 3. Executando os Testes via CLI

O framework agora conta com uma linha de comando profissional (CLI) para instalar dependências e rodar tudo de forma limpa.

### Instalar a infraestrutura no seu projeto:
Na raiz do seu projeto, clone este repositório (com o nome que preferir, por exemplo, `arm-hil-semihost` ou `test_engine`) e rode o script de instalação.

```bash
# Baixa o repositório dentro da sua pasta
git clone https://github.com/stephan-biomedical-engineer/arm-hil-semihost.git

# Roda o instalador apontando para a pasta recém-baixada
python3 arm-hil-semihost/hil_tool/hil_cli.py install
```
O script se adaptará automaticamente ao nome da pasta que você escolheu!

### Rodar a bateria de testes:
Sempre que quiser compilar, flashear o microcontrolador e coletar os dados:
```bash
python3 arm-hil-semihost/hil_tool/hil_cli.py run
```
**O que acontece por trás das cortinas?**
1. O CLI invoca seu `Makefile` ou `CMake`.
2. O código fonte será compilado com a flag que ativa a API HIL.
3. O script injeta o binário na placa.
4. O Python captura os pacotes de semihosting contendo `[ PASS ]` e `[ FAIL ]`.

---

## 4. Avançado: Injeção de Funções (Inferior Function Call)

Se você não quer escrever a lógica do teste dentro do C, mas sim "empurrar" valores para o microcontrolador de forma dinâmica, você pode usar a nossa biblioteca de RPC (Remote Procedure Call). 

Isso é excelente para testes pontuais rápidos, calibração ou *Mocks*. A execução do RPC é 100% automatizada e não exige que você saiba programar scripts extras em Python!

### 4.1 Definindo os Testes em JSON
Crie um arquivo na raiz do seu projeto chamado `rpc_tests.json`. Nele você diz quais funções em C quer testar e quais argumentos passar.

```json
{
    "tests": [
        {
            "name": "Soma Basica Injetada via RPC",
            "function": "rpc_soma_teste",
            "args": [15, 10],
            "expected": 40
        }
    ]
}
```

### 4.2 Rodando a Mágica
Basta chamar o subcomando `rpc` pelo nosso CLI. O framework cuidará de mapear os endereços da memória, conectar-se fisicamente ao ST-Link via pyOCD e orquestrar a Injeção.

```bash
python3 arm-hil-semihost/hil_tool/hil_cli.py rpc --tests rpc_tests.json
```

O CLI vai parar a CPU do STM32 subitamente, forçar os registradores a calcularem a sua função, verificar se o microcontrolador retornou `40`, imprimir `[ PASS ]` e depois devolver o sistema ao estado de execução natural, como se nada tivesse acontecido!
