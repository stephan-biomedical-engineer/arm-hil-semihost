import os
import json

def load_config(app_path):
    """
    Procura por hil.yaml ou hil.json na pasta especificada.
    Se ambos existirem, o hil.yaml tem precedência.
    Retorna um dicionário com as configurações, ou um dicionário vazio.
    """
    config = {}
    
    yaml_path = os.path.join(app_path, "hil.yaml")
    json_path = os.path.join(app_path, "hil.json")

    if os.path.exists(yaml_path):
        try:
            import yaml
            with open(yaml_path, 'r') as f:
                parsed = yaml.safe_load(f)
                if parsed:
                    config = parsed
                    return config
        except ImportError:
            print("[!] Aviso: PyYAML não instalado. Execute pip install pyyaml para ler hil.yaml")
            print("[!] Tentando ler hil.json como fallback...")
        except Exception as e:
            print(f"[!] ERRO ao ler {yaml_path}: {e}")

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                parsed = json.load(f)
                if parsed:
                    config = parsed
                    return config
        except Exception as e:
            print(f"[!] ERRO ao ler {json_path}: {e}")

    return config

def override_args(args, config, sys_argv):
    """
    Substitui os valores padrão do argparse pelos valores do arquivo de configuração,
    A MENOS que o argumento tenha sido explicitamente passado via linha de comando.
    """
    # Mapeamento dos parâmetros do arquivo para os argumentos da CLI
    param_map = {
        'flash_backend': '--flash-backend',
        'probe': '--probe',
        'timeout': '--timeout',
        'stm32_cli_path': '--stm32-cli-path',
        'report_xml': '--report-xml',
        'report_json': '--report-json'
    }

    for key, flag in param_map.items():
        if key in config and not sys_argv.count(flag):
            setattr(args, key, config[key])

    # Booleano especial
    if 'auto_dump' in config and not sys_argv.count('--no-auto-dump'):
        # args.no_auto_dump armazena se vamos desativar. 
        # Então se auto_dump no arquivo for false, no_auto_dump deve ser True.
        args.no_auto_dump = not config['auto_dump']

    return args
