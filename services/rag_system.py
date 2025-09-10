"""
RAG (Retrieval Augmented Generation) System para SolarMind

Sistema de conhecimento contextual que permite ao chat AI responder
com base no código, documentação e funcionalidades específicas do projeto.

Features:
- Extração automática de conhecimento do projeto
- Busca vetorial de contexto relevante  
- Respostas contextualizadas do Gemini
- Base de conhecimento sempre atualizada
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class ProjectKnowledgeBase:
    """
    Extrai e indexa conhecimento do projeto SolarMind.
    
    Analisa:
    - Código Python (funcionalidades, classes, métodos)
    - Templates HTML (interfaces, forms)
    - Documentação (READMEs, comentários)
    - Configurações (env, configs)
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.knowledge_file = self.project_root / 'instance' / 'project_knowledge.json'
        self.knowledge_cache = {}
        self.last_update = None
        
    def extract_project_knowledge(self) -> Dict[str, Any]:
        """
        Extrai conhecimento completo do projeto.
        
        Returns:
            Dict: Base de conhecimento estruturada
        """
        logger.info("🧠 Extraindo conhecimento do projeto SolarMind...")
        
        knowledge = {
            'project_info': self._get_project_info(),
            'features': self._extract_features(),
            'api_endpoints': self._extract_api_endpoints(),
            'models': self._extract_models(),
            'services': self._extract_services(),
            'templates': self._extract_templates(),
            'configurations': self._extract_configurations(),
            'documentation': self._extract_documentation(),
            'generated_at': datetime.now().isoformat(),
            'version': '2.0.0'
        }
        
        # Salva na cache e arquivo
        self.knowledge_cache = knowledge
        self._save_knowledge(knowledge)
        
        logger.info(f"✅ Conhecimento extraído: {len(knowledge)} categorias")
        return knowledge
    
    def _get_project_info(self) -> Dict[str, Any]:
        """Informações básicas do projeto."""
        return {
            'name': 'SolarMind',
            'description': 'Sistema Inteligente de Monitoramento Solar com IA',
            'main_features': [
                'Monitoramento solar em tempo real',
                'Chat AI com Gemini',
                'Energy Autopilot',
                'Integração IFTTT/Alexa',
                'Dashboard interativo',
                'Scheduler automático',
                'Gestão de aparelhos'
            ],
            'tech_stack': [
                'Python/Flask',
                'SQLite/SQLAlchemy', 
                'Google Gemini AI',
                'APScheduler',
                'Flask-Login',
                'Bootstrap/JavaScript',
                'IFTTT Integration'
            ]
        }
    
    def _extract_features(self) -> List[Dict[str, Any]]:
        """Extrai funcionalidades dos arquivos de rotas."""
        features = []
        
        routes_dir = self.project_root / 'routes'
        if not routes_dir.exists():
            return features
            
        for py_file in routes_dir.glob('*.py'):
            if py_file.name == '__init__.py':
                continue
                
            content = self._read_file_safe(py_file)
            if not content:
                continue
                
            # Extrai rotas e funcionalidades
            routes = self._extract_routes_from_file(content, py_file.name)
            features.extend(routes)
            
        return features
    
    def _extract_routes_from_file(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Extrai rotas e suas funcionalidades de um arquivo."""
        routes = []
        
        # Regex para encontrar decorators de rota
        route_pattern = r'@\w+\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?\)'
        function_pattern = r'def\s+(\w+)\([^)]*\):\s*"""([^"]*?)"""'
        
        route_matches = re.finditer(route_pattern, content)
        func_matches = re.finditer(function_pattern, content, re.DOTALL)
        
        # Mapeia funções para suas rotas
        for route_match in route_matches:
            route_path = route_match.group(1)
            methods = route_match.group(2) if route_match.group(2) else 'GET'
            
            # Encontra a função correspondente
            start_pos = route_match.end()
            next_func = re.search(r'def\s+(\w+)\([^)]*\):\s*(?:"""([^"]*?)""")?(.*?)(?=@|\Z)', 
                                content[start_pos:], re.DOTALL)
            
            if next_func:
                func_name = next_func.group(1)
                docstring = next_func.group(2) or ''
                func_body = next_func.group(3) or ''
                
                routes.append({
                    'file': filename,
                    'route': route_path,
                    'methods': methods.replace("'", "").replace('"', '').split(', '),
                    'function': func_name,
                    'description': docstring.strip(),
                    'functionality': self._analyze_function_body(func_body)
                })
                
        return routes
    
    def _analyze_function_body(self, func_body: str) -> List[str]:
        """Analisa o corpo da função para extrair funcionalidades."""
        features = []
        
        # Padrões comuns de funcionalidades
        patterns = {
            'database': r'(\.query\.|\.filter\.|\.add\(|\.commit\()',
            'api_call': r'(requests\.|urllib\.|fetch)',
            'template_render': r'render_template\(',
            'json_response': r'jsonify\(',
            'file_operations': r'(open\(|\.read\(|\.write\()',
            'scheduler': r'(scheduler\.|APScheduler)',
            'gemini_ai': r'(gemini_client|GeminiClient)',
            'ifttt': r'(ifttt|webhook)',
            'authentication': r'(login_required|session\[)',
            'validation': r'(validate|check|verify)'
        }
        
        for feature_type, pattern in patterns.items():
            if re.search(pattern, func_body, re.IGNORECASE):
                features.append(feature_type)
                
        return features
    
    def _extract_api_endpoints(self) -> List[Dict[str, Any]]:
        """Extrai todos os endpoints da API."""
        endpoints = []
        
        api_file = self.project_root / 'routes' / 'api.py'
        if not api_file.exists():
            return endpoints
            
        content = self._read_file_safe(api_file)
        if not content:
            return endpoints
            
        # Padrão específico para endpoints API
        api_pattern = r'@api_bp\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?\)\s*(?:@\w+\s*)*def\s+(\w+)\([^)]*\):\s*(?:"""([^"]*?)""")?'
        
        matches = re.finditer(api_pattern, content, re.DOTALL)
        
        for match in matches:
            endpoints.append({
                'path': match.group(1),
                'methods': match.group(2).replace("'", "").replace('"', '').split(', ') if match.group(2) else ['GET'],
                'function': match.group(3),
                'description': match.group(4).strip() if match.group(4) else '',
                'category': self._categorize_endpoint(match.group(1))
            })
            
        return endpoints
    
    def _categorize_endpoint(self, path: str) -> str:
        """Categoriza endpoint baseado no path."""
        if '/api/ia/' in path or '/api/gemini/' in path:
            return 'AI/Gemini'
        elif '/api/chat/' in path:
            return 'Chat'
        elif '/api/scheduler/' in path:
            return 'Scheduler'
        elif '/api/alertas/' in path:
            return 'Alertas'
        elif '/api/automacao/' in path:
            return 'Automação'
        elif '/ifttt/' in path:
            return 'IFTTT'
        else:
            return 'Geral'
    
    def _extract_models(self) -> List[Dict[str, Any]]:
        """Extrai modelos do banco de dados."""
        models = []
        
        models_dir = self.project_root / 'models'
        if not models_dir.exists():
            return models
            
        for py_file in models_dir.glob('*.py'):
            if py_file.name == '__init__.py':
                continue
                
            content = self._read_file_safe(py_file)
            if not content:
                continue
                
            # Extrai classes de modelo
            class_pattern = r'class\s+(\w+)\([^)]*\):\s*(?:"""([^"]*?)""")?'
            matches = re.finditer(class_pattern, content, re.DOTALL)
            
            for match in matches:
                class_name = match.group(1)
                docstring = match.group(2) or ''
                
                # Extrai campos do modelo
                fields = self._extract_model_fields(content, match.end())
                
                models.append({
                    'name': class_name,
                    'file': py_file.name,
                    'description': docstring.strip(),
                    'fields': fields
                })
                
        return models
    
    def _extract_model_fields(self, content: str, start_pos: int) -> List[Dict[str, str]]:
        """Extrai campos de um modelo SQLAlchemy."""
        fields = []
        
        # Padrão para campos SQLAlchemy
        field_pattern = r'(\w+)\s*=\s*db\.Column\(([^)]+)\)'
        
        # Pega o texto da classe até a próxima classe ou final
        class_text = content[start_pos:]
        next_class = re.search(r'\nclass\s+', class_text)
        if next_class:
            class_text = class_text[:next_class.start()]
            
        matches = re.finditer(field_pattern, class_text)
        
        for match in matches:
            field_name = match.group(1)
            field_type = match.group(2).split(',')[0].strip()
            
            fields.append({
                'name': field_name,
                'type': field_type,
                'definition': match.group(2)
            })
            
        return fields
    
    def _extract_services(self) -> List[Dict[str, Any]]:
        """Extrai serviços do diretório services/."""
        services = []
        
        services_dir = self.project_root / 'services'
        if not services_dir.exists():
            return services
            
        for py_file in services_dir.glob('*.py'):
            if py_file.name == '__init__.py':
                continue
                
            content = self._read_file_safe(py_file)
            if not content:
                continue
                
            # Extrai classes principais e funções
            classes = self._extract_classes(content)
            functions = self._extract_functions(content)
            
            services.append({
                'name': py_file.stem,
                'file': py_file.name,
                'classes': classes,
                'functions': functions,
                'purpose': self._infer_service_purpose(py_file.stem, content)
            })
            
        return services
    
    def _extract_classes(self, content: str) -> List[Dict[str, str]]:
        """Extrai classes de um arquivo."""
        classes = []
        
        class_pattern = r'class\s+(\w+)(?:\([^)]*\))?\s*:\s*(?:"""([^"]*?)""")?'
        matches = re.finditer(class_pattern, content, re.DOTALL)
        
        for match in matches:
            classes.append({
                'name': match.group(1),
                'description': match.group(2).strip() if match.group(2) else ''
            })
            
        return classes
    
    def _extract_functions(self, content: str) -> List[Dict[str, str]]:
        """Extrai funções de um arquivo."""
        functions = []
        
        func_pattern = r'def\s+(\w+)\([^)]*\):\s*(?:"""([^"]*?)""")?'
        matches = re.finditer(func_pattern, content, re.DOTALL)
        
        for match in matches:
            if not match.group(1).startswith('_'):  # Ignora métodos privados
                functions.append({
                    'name': match.group(1),
                    'description': match.group(2).strip() if match.group(2) else ''
                })
                
        return functions
    
    def _infer_service_purpose(self, filename: str, content: str) -> str:
        """Infere o propósito de um serviço baseado no nome e conteúdo."""
        purposes = {
            'gemini_client': 'Integração com Google Gemini AI para chat e insights',
            'scheduler': 'Agendamento automático de tarefas (resumos, autopilot)',
            'automacao': 'Automação residencial e controle de aparelhos',
            'goodwe_client': 'Cliente para API GoodWe/SEMS',
            'simula_evento': 'Simulação de eventos e dados para testes'
        }
        
        if filename in purposes:
            return purposes[filename]
            
        # Inferência baseada no conteúdo
        if 'gemini' in content.lower():
            return 'Integração com IA Gemini'
        elif 'scheduler' in content.lower():
            return 'Agendamento de tarefas'
        elif 'ifttt' in content.lower():
            return 'Integração IFTTT'
        else:
            return 'Serviço do sistema'
    
    def _extract_templates(self) -> List[Dict[str, Any]]:
        """Extrai informações dos templates HTML."""
        templates = []
        
        templates_dir = self.project_root / 'templates'
        if not templates_dir.exists():
            return templates
            
        for html_file in templates_dir.glob('*.html'):
            content = self._read_file_safe(html_file)
            if not content:
                continue
                
            templates.append({
                'name': html_file.stem,
                'file': html_file.name,
                'purpose': self._infer_template_purpose(html_file.stem),
                'forms': self._extract_html_forms(content),
                'features': self._extract_html_features(content)
            })
            
        return templates
    
    def _infer_template_purpose(self, filename: str) -> str:
        """Infere o propósito de um template."""
        purposes = {
            'base': 'Template base com layout comum',
            'login': 'Página de login de usuários',
            'register': 'Página de registro de usuários',
            'dashboard': 'Dashboard principal com métricas',
            'chat': 'Interface de chat com IA',
            'aparelhos': 'Gestão de aparelhos residenciais',
            'estatisticas': 'Página de estatísticas e relatórios',
            'home': 'Página inicial do sistema'
        }
        
        return purposes.get(filename, f'Página {filename}')
    
    def _extract_html_forms(self, content: str) -> List[Dict[str, Any]]:
        """Extrai formulários HTML."""
        forms = []
        
        form_pattern = r'<form[^>]*action=[\'"]([^\'"]*)[\'"][^>]*>(.*?)</form>'
        matches = re.finditer(form_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            action = match.group(1)
            form_content = match.group(2)
            
            # Extrai campos do formulário
            fields = self._extract_form_fields(form_content)
            
            forms.append({
                'action': action,
                'fields': fields
            })
            
        return forms
    
    def _extract_form_fields(self, form_content: str) -> List[str]:
        """Extrai campos de um formulário."""
        fields = []
        
        input_pattern = r'<input[^>]*name=[\'"]([^\'"]*)[\'"][^>]*>'
        matches = re.finditer(input_pattern, form_content, re.IGNORECASE)
        
        for match in matches:
            fields.append(match.group(1))
            
        return fields
    
    def _extract_html_features(self, content: str) -> List[str]:
        """Identifica features presentes no HTML."""
        features = []
        
        feature_patterns = {
            'charts': r'(Chart\.js|chart|graph)',
            'modals': r'(modal|Modal)',
            'ajax': r'(ajax|fetch|XMLHttpRequest)',
            'chat': r'(chat|message)',
            'forms': r'(<form|input|button)',
            'tables': r'(<table|datatable)',
            'cards': r'(card|panel)',
            'navigation': r'(navbar|nav|menu)'
        }
        
        for feature, pattern in feature_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                features.append(feature)
                
        return features
    
    def _extract_configurations(self) -> Dict[str, Any]:
        """Extrai configurações do projeto."""
        configs = {}
        
        # .env.example
        env_example = self.project_root / '.env.example'
        if env_example.exists():
            content = self._read_file_safe(env_example)
            configs['environment_variables'] = self._parse_env_file(content)
        
        # requirements.txt
        requirements = self.project_root / 'requirements.txt'
        if requirements.exists():
            content = self._read_file_safe(requirements)
            if content:
                configs['dependencies'] = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        # config.py
        config_file = self.project_root / 'config.py'
        if config_file.exists():
            content = self._read_file_safe(config_file)
            configs['flask_config'] = self._extract_flask_config(content)
            
        return configs
    
    def _parse_env_file(self, content: str) -> List[Dict[str, str]]:
        """Parse arquivo .env para extrair variáveis."""
        variables = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                variables.append({
                    'key': key.strip(),
                    'example_value': value.strip(),
                    'category': self._categorize_env_var(key.strip())
                })
                
        return variables
    
    def _categorize_env_var(self, key: str) -> str:
        """Categoriza variável de ambiente."""
        if 'GEMINI' in key:
            return 'Gemini AI'
        elif 'IFTTT' in key or 'WEBHOOK' in key:
            return 'IFTTT'
        elif 'SEMS' in key or 'GOODWE' in key:
            return 'GoodWe/SEMS'
        elif 'SECRET' in key or 'KEY' in key:
            return 'Segurança'
        elif 'DB' in key or 'DATABASE' in key:
            return 'Banco de Dados'
        elif 'SCHEDULER' in key or 'TIME' in key:
            return 'Scheduler'
        else:
            return 'Geral'
    
    def _extract_flask_config(self, content: str) -> List[str]:
        """Extrai configurações do Flask."""
        configs = []
        
        config_pattern = r'(\w+)\s*=\s*([^\n]+)'
        matches = re.finditer(config_pattern, content)
        
        for match in matches:
            configs.append(f"{match.group(1)} = {match.group(2)}")
            
        return configs
    
    def _extract_documentation(self) -> List[Dict[str, str]]:
        """Extrai documentação do projeto."""
        docs = []
        
        # README files
        for readme in self.project_root.glob('*.md'):
            content = self._read_file_safe(readme)
            if content:
                docs.append({
                    'file': readme.name,
                    'type': 'markdown',
                    'content': content[:2000] + '...' if len(content) > 2000 else content
                })
        
        # Docstrings dos arquivos principais
        for py_file in self.project_root.glob('*.py'):
            content = self._read_file_safe(py_file)
            if content:
                docstring = self._extract_module_docstring(content)
                if docstring:
                    docs.append({
                        'file': py_file.name,
                        'type': 'docstring',
                        'content': docstring
                    })
                    
        return docs
    
    def _extract_module_docstring(self, content: str) -> Optional[str]:
        """Extrai docstring de módulo."""
        docstring_pattern = r'^(?:\s*#[^\n]*\n)*\s*"""([^"]*?)"""'
        match = re.search(docstring_pattern, content, re.DOTALL | re.MULTILINE)
        
        if match:
            return match.group(1).strip()
        return None
    
    def _read_file_safe(self, file_path: Path) -> Optional[str]:
        """Lê arquivo de forma segura."""
        try:
            # Tenta UTF-8 primeiro
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Fallback para latin-1
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Erro ao ler {file_path} com latin-1: {e}")
                return None
        except Exception as e:
            logger.warning(f"Erro ao ler {file_path}: {e}")
            return None
    
    def _save_knowledge(self, knowledge: Dict[str, Any]):
        """Salva base de conhecimento em arquivo."""
        try:
            os.makedirs(self.knowledge_file.parent, exist_ok=True)
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Base de conhecimento salva em {self.knowledge_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar base de conhecimento: {e}")
    
    def load_knowledge(self) -> Dict[str, Any]:
        """Carrega base de conhecimento do arquivo."""
        if self.knowledge_cache:
            return self.knowledge_cache
            
        try:
            if self.knowledge_file.exists():
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                self.knowledge_cache = knowledge
                return knowledge
        except Exception as e:
            logger.error(f"Erro ao carregar base de conhecimento: {e}")
            
        # Se não conseguir carregar, extrai novamente
        return self.extract_project_knowledge()
    
    def get_relevant_context(self, query: str, max_items: int = 5) -> List[Dict[str, Any]]:
        """
        Busca contexto relevante para uma query.
        
        Args:
            query: Pergunta/query do usuário
            max_items: Máximo de itens de contexto
            
        Returns:
            List: Contexto relevante para a query
        """
        knowledge = self.load_knowledge()
        relevant_context = []
        
        query_lower = query.lower()
        
        # Busca em diferentes categorias
        context_searches = [
            ('features', self._search_features, knowledge.get('features', [])),
            ('api_endpoints', self._search_endpoints, knowledge.get('api_endpoints', [])),
            ('models', self._search_models, knowledge.get('models', [])),
            ('services', self._search_services, knowledge.get('services', [])),
            ('documentation', self._search_documentation, knowledge.get('documentation', []))
        ]
        
        for category, search_func, data in context_searches:
            matches = search_func(query_lower, data)
            for match in matches[:max_items]:
                relevant_context.append({
                    'category': category,
                    'relevance': match.get('relevance', 0.5),
                    'content': match
                })
        
        # Ordena por relevância e retorna os mais relevantes
        relevant_context.sort(key=lambda x: x['relevance'], reverse=True)
        return relevant_context[:max_items]
    
    def _search_features(self, query: str, features: List[Dict]) -> List[Dict]:
        """Busca features relevantes."""
        matches = []
        
        for feature in features:
            relevance = 0
            
            # Busca na rota
            if any(term in feature.get('route', '').lower() for term in query.split()):
                relevance += 0.8
                
            # Busca na descrição
            if any(term in feature.get('description', '').lower() for term in query.split()):
                relevance += 0.6
                
            # Busca na funcionalidade
            if any(term in str(feature.get('functionality', [])).lower() for term in query.split()):
                relevance += 0.4
            
            if relevance > 0:
                feature['relevance'] = relevance
                matches.append(feature)
                
        return matches
    
    def _search_endpoints(self, query: str, endpoints: List[Dict]) -> List[Dict]:
        """Busca endpoints relevantes."""
        matches = []
        
        for endpoint in endpoints:
            relevance = 0
            
            if any(term in endpoint.get('path', '').lower() for term in query.split()):
                relevance += 0.9
                
            if any(term in endpoint.get('description', '').lower() for term in query.split()):
                relevance += 0.7
                
            if any(term in endpoint.get('category', '').lower() for term in query.split()):
                relevance += 0.5
            
            if relevance > 0:
                endpoint['relevance'] = relevance
                matches.append(endpoint)
                
        return matches
    
    def _search_models(self, query: str, models: List[Dict]) -> List[Dict]:
        """Busca modelos relevantes."""
        matches = []
        
        for model in models:
            relevance = 0
            
            if any(term in model.get('name', '').lower() for term in query.split()):
                relevance += 0.8
                
            if any(term in model.get('description', '').lower() for term in query.split()):
                relevance += 0.6
                
            # Busca nos campos
            for field in model.get('fields', []):
                if any(term in field.get('name', '').lower() for term in query.split()):
                    relevance += 0.3
            
            if relevance > 0:
                model['relevance'] = relevance
                matches.append(model)
                
        return matches
    
    def _search_services(self, query: str, services: List[Dict]) -> List[Dict]:
        """Busca serviços relevantes."""
        matches = []
        
        for service in services:
            relevance = 0
            
            if any(term in service.get('name', '').lower() for term in query.split()):
                relevance += 0.8
                
            if any(term in service.get('purpose', '').lower() for term in query.split()):
                relevance += 0.7
                
            # Busca nas classes e funções
            for cls in service.get('classes', []):
                if any(term in cls.get('name', '').lower() for term in query.split()):
                    relevance += 0.4
                    
            for func in service.get('functions', []):
                if any(term in func.get('name', '').lower() for term in query.split()):
                    relevance += 0.3
            
            if relevance > 0:
                service['relevance'] = relevance
                matches.append(service)
                
        return matches
    
    def _search_documentation(self, query: str, docs: List[Dict]) -> List[Dict]:
        """Busca documentação relevante."""
        matches = []
        
        for doc in docs:
            relevance = 0
            
            if any(term in doc.get('content', '').lower() for term in query.split()):
                relevance += 0.5
                
            if any(term in doc.get('file', '').lower() for term in query.split()):
                relevance += 0.7
            
            if relevance > 0:
                doc['relevance'] = relevance
                matches.append(doc)
                
        return matches


class RAGSystem:
    """
    Sistema RAG completo que combina busca de contexto com Gemini AI.
    """
    
    def __init__(self):
        self.knowledge_base = ProjectKnowledgeBase()
        
    def get_contextual_response(self, query: str, user_context: Dict = None) -> Dict[str, Any]:
        """
        Gera resposta contextual usando RAG + Gemini.
        
        Args:
            query: Pergunta do usuário
            user_context: Contexto adicional do usuário
            
        Returns:
            Dict: Resposta com contexto e metadados
        """
        try:
            # 1. Busca contexto relevante no projeto
            relevant_context = self.knowledge_base.get_relevant_context(query, max_items=3)
            
            # 2. Constrói prompt contextual
            context_prompt = self._build_context_prompt(query, relevant_context, user_context)
            
            # 3. Chama Gemini com contexto
            from services.gemini_client import GeminiClient
            gemini = GeminiClient()
            
            if not gemini.is_enabled():
                return {
                    'response': 'Sistema RAG não disponível (Gemini desabilitado)',
                    'context_used': [],
                    'error': 'Gemini não configurado'
                }
                
            response = gemini._make_request(context_prompt)
            
            if response and response.get('success'):
                return {
                    'response': response['content'],
                    'context_used': [ctx['category'] for ctx in relevant_context],
                    'relevance_score': sum(ctx['relevance'] for ctx in relevant_context) / len(relevant_context) if relevant_context else 0,
                    'source': 'RAG + Gemini'
                }
            else:
                return {
                    'response': 'Erro ao gerar resposta contextual',
                    'context_used': [],
                    'error': response.get('error', 'Erro desconhecido') if response else 'Falha na comunicação'
                }
                
        except Exception as e:
            logger.error(f"Erro no sistema RAG: {e}")
            return {
                'response': 'Erro interno do sistema RAG',
                'context_used': [],
                'error': str(e)
            }
    
    def _build_context_prompt(self, query: str, context: List[Dict], user_context: Dict = None) -> str:
        """Constrói prompt com contexto para o Gemini."""
        
        prompt = f"""Você é o assistente AI especialista no SolarMind, um sistema inteligente de monitoramento solar.

CONTEXTO DO PROJETO:
- SolarMind é um sistema Flask para monitoramento de energia solar
- Possui integração com IA (Gemini), automação residencial, IFTTT/Alexa
- Features: dashboard, chat AI, scheduler automático, gestão de aparelhos
- Tecnologias: Python/Flask, SQLite, Google Gemini, Bootstrap

CONTEXTO ESPECÍFICO PARA ESTA PERGUNTA:
"""
        
        # Adiciona contexto relevante encontrado
        for i, ctx in enumerate(context, 1):
            prompt += f"\n{i}. {ctx['category'].upper()}:\n"
            
            if ctx['category'] == 'features':
                content = ctx['content']
                prompt += f"   - Rota: {content.get('route', 'N/A')}\n"
                prompt += f"   - Função: {content.get('function', 'N/A')}\n"
                prompt += f"   - Descrição: {content.get('description', 'N/A')}\n"
                prompt += f"   - Funcionalidades: {', '.join(content.get('functionality', []))}\n"
                
            elif ctx['category'] == 'api_endpoints':
                content = ctx['content']
                prompt += f"   - Endpoint: {content.get('path', 'N/A')}\n"
                prompt += f"   - Métodos: {', '.join(content.get('methods', []))}\n"
                prompt += f"   - Categoria: {content.get('category', 'N/A')}\n"
                prompt += f"   - Descrição: {content.get('description', 'N/A')}\n"
                
            elif ctx['category'] == 'services':
                content = ctx['content']
                prompt += f"   - Serviço: {content.get('name', 'N/A')}\n"
                prompt += f"   - Propósito: {content.get('purpose', 'N/A')}\n"
                prompt += f"   - Classes: {', '.join([c['name'] for c in content.get('classes', [])])}\n"
                
            elif ctx['category'] == 'models':
                content = ctx['content']
                prompt += f"   - Modelo: {content.get('name', 'N/A')}\n"
                prompt += f"   - Descrição: {content.get('description', 'N/A')}\n"
                prompt += f"   - Campos: {', '.join([f['name'] for f in content.get('fields', [])])}\n"
        
        # Adiciona contexto do usuário se disponível
        if user_context:
            prompt += f"\nCONTEXTO DO USUÁRIO:\n"
            if user_context.get('energia_gerada'):
                prompt += f"- Energia gerada: {user_context['energia_gerada']} kWh\n"
            if user_context.get('energia_consumida'):
                prompt += f"- Energia consumida: {user_context['energia_consumida']} kWh\n"
            if user_context.get('soc_bateria'):
                prompt += f"- SOC bateria: {user_context['soc_bateria']}%\n"
        
        prompt += f"""

PERGUNTA DO USUÁRIO: {query}

INSTRUÇÕES:
1. Responda especificamente sobre o SolarMind baseado no contexto fornecido
2. Use exemplos práticos das funcionalidades reais do sistema
3. Se for sobre configuração, mencione arquivos específicos (.env, etc.)
4. Se for sobre uso, explique os passos exatos no sistema
5. Seja técnico mas didático
6. Foque na informação mais relevante do contexto
7. Se não souber algo específico, diga que pode consultar a documentação

Responda de forma útil e específica ao SolarMind:"""

        return prompt
    
    def rebuild_knowledge_base(self) -> Dict[str, Any]:
        """Reconstrói a base de conhecimento do projeto."""
        logger.info("🔄 Reconstruindo base de conhecimento...")
        return self.knowledge_base.extract_project_knowledge()


# Instância global do sistema RAG
rag_system = RAGSystem()
