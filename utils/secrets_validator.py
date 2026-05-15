"""Utilitário para validação e gerenciamento seguro de secrets.

Este módulo implementa boas práticas de segurança para validação de API keys,
tokens e outras credenciais usadas no NKAssist.
"""

import os
import re
from typing import Optional, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SecretsValidator:
    """Validador de secrets com detecção de padrões inseguros."""
    
    # Padrões de secrets conhecidos (para detecção, não para uso!)
    SECRET_PATTERNS = {
        'openai_key': r'sk-[A-Za-z0-9]{48}',
        'anthropic_key': r'sk-ant-[A-Za-z0-9\-]{95}',
        'aws_access': r'AKIA[0-9A-Z]{16}',
        'github_token': r'ghp_[A-Za-z0-9]{36}',
        'generic_api_key': r'api[_-]?key[\s]*[=:][\s]*['\"][A-Za-z0-9]{20,}['\"]'
    }
    
    # Variáveis de ambiente obrigatórias
    REQUIRED_ENV_VARS = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY'
    ]
    
    @staticmethod
    def validate_env_vars() -> Dict[str, bool]:
        """Valida se todas as variáveis de ambiente necessárias estão configuradas."""
        results = {}
        for var in SecretsValidator.REQUIRED_ENV_VARS:
            value = os.getenv(var)
            is_valid = value is not None and len(value) > 10
            results[var] = is_valid
            
            if not is_valid:
                logger.warning(f"Variável de ambiente {var} não configurada ou inválida")
        
        return results
    
    @staticmethod
    def scan_code_for_secrets(file_path: Path) -> List[Dict[str, str]]:
        """Escaneia arquivo em busca de secrets expostos acidentalmente."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for secret_type, pattern in SecretsValidator.SECRET_PATTERNS.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    findings.append({
                        'type': secret_type,
                        'file': str(file_path),
                        'position': match.start(),
                        'preview': match.group()[:20] + '...'
                    })
                    logger.error(
                        f"SECRET DETECTADO: {secret_type} em {file_path}"
                    )
        
        except Exception as e:
            logger.error(f"Erro ao escanear {file_path}: {e}")
        
        return findings
    
    @staticmethod
    def mask_secret(secret: str, visible_chars: int = 4) -> str:
        """Mascara um secret para log seguro."""
        if not secret or len(secret) <= visible_chars:
            return '***'
        
        return secret[:visible_chars] + '*' * (len(secret) - visible_chars)
    
    @staticmethod
    def load_secret_safely(env_var: str, default: Optional[str] = None) -> Optional[str]:
        """Carrega secret de forma segura com validação."""
        value = os.getenv(env_var, default)
        
        if value is None:
            logger.error(f"Secret {env_var} não encontrado")
            return None
        
        # Valida comprimento mínimo
        if len(value) < 10:
            logger.warning(f"Secret {env_var} muito curto - possível erro")
            return None
        
        logger.info(f"Secret {env_var} carregado: {SecretsValidator.mask_secret(value)}")
        return value


def validate_project_secrets() -> bool:
    """Valida todos os secrets do projeto."""
    validator = SecretsValidator()
    results = validator.validate_env_vars()
    
    all_valid = all(results.values())
    
    if all_valid:
        logger.info("✅ Todos os secrets configurados corretamente")
    else:
        missing = [k for k, v in results.items() if not v]
        logger.error(f"❌ Secrets faltando ou inválidos: {missing}")
    
    return all_valid


if __name__ == '__main__':
    # Exemplo de uso
    logging.basicConfig(level=logging.INFO)
    validate_project_secrets()
