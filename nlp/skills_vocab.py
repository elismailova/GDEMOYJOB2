"""Словарь навыков для извлечения из резюме и описаний вакансий."""

TECH_SKILLS: set[str] = {
    # Языки программирования
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "kotlin", "swift", "ruby", "php", "scala", "r", "matlab", "perl",
    "bash", "shell", "powershell", "dart", "lua", "haskell", "elixir",
    # Web frontend
    "html", "css", "react", "vue", "angular", "svelte", "nextjs", "nuxtjs",
    "webpack", "vite", "tailwind", "bootstrap", "sass", "scss", "jquery",
    "redux", "mobx", "zustand", "graphql", "rest", "rest api", "api",
    # Web backend
    "django", "flask", "fastapi", "aiohttp", "tornado", "express", "nestjs",
    "spring", "spring boot", "laravel", "rails", "asp.net", "gin", "fiber",
    "node.js", "nodejs", "deno", "bun",
    # БД и хранилища
    "postgresql", "postgres", "mysql", "sqlite", "mariadb", "oracle",
    "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "clickhouse",
    "neo4j", "influxdb", "hbase", "couchdb", "firebase",
    "sql", "nosql", "orm", "sqlalchemy", "hibernate", "prisma", "sequelize",
    # DevOps / инфраструктура
    "docker", "kubernetes", "k8s", "helm", "terraform", "ansible", "puppet",
    "jenkins", "gitlab ci", "github actions", "circleci", "travis ci",
    "nginx", "apache", "caddy", "linux", "ubuntu", "centos", "debian",
    "aws", "azure", "gcp", "google cloud", "digitalocean", "heroku",
    "s3", "ec2", "lambda", "cloudformation", "vpc",
    "prometheus", "grafana", "kibana", "elk", "splunk", "datadog",
    # Очереди сообщений
    "kafka", "rabbitmq", "celery", "redis queue", "nats", "activemq",
    # ML / Data Science
    "machine learning", "deep learning", "neural networks", "nlp",
    "computer vision", "cv", "pytorch", "tensorflow", "keras", "sklearn",
    "scikit-learn", "xgboost", "lightgbm", "catboost", "huggingface",
    "transformers", "bert", "gpt", "llm", "pandas", "numpy", "scipy",
    "matplotlib", "seaborn", "plotly", "jupyter", "spark", "hadoop",
    "airflow", "dbt", "mlflow", "kubeflow", "feature engineering",
    "data analysis", "data science", "statistics", "statistical analysis",
    # Тестирование
    "pytest", "unittest", "jest", "mocha", "cypress", "selenium",
    "playwright", "testng", "junit", "tdd", "bdd", "qa",
    # Архитектура и паттерны
    "microservices", "monolith", "ddd", "clean architecture", "solid",
    "design patterns", "mvc", "mvvm", "cqrs", "event sourcing",
    "grpc", "websocket", "oauth", "jwt", "oauth2",
    # Мобильная разработка
    "android", "ios", "react native", "flutter", "xamarin",
    # Инструменты разработки
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "figma", "photoshop", "trello", "notion",
    # Офисные и бизнес-инструменты
    "excel", "microsoft excel", "word", "powerpoint", "outlook",
    "microsoft office", "ms office", "google sheets", "google docs",
    "power bi", "tableau", "qlik", "looker",
    "1с", "1c", "1с:предприятие", "sap", "erp", "crm",
    # Сокращения и алиасы
    "js", "ts", "py", "cpp", "cs", "vba", "sql server", "ms sql",
    "postgresql", "mysql", "nosql",
    # Безопасность
    "cybersecurity", "penetration testing", "owasp", "ssl", "tls",
    "encryption", "cryptography", "sso", "ldap", "active directory",
}

SOFT_SKILLS: set[str] = {
    "teamwork", "team player", "leadership", "communication", "problem solving",
    "time management", "critical thinking", "creativity", "adaptability",
    "attention to detail", "multitasking", "project management",
    "agile", "scrum", "kanban", "работа в команде", "лидерство",
    "коммуникация", "управление проектами", "аналитическое мышление",
    "креативность", "адаптивность", "тайм-менеджмент", "ответственность",
    "инициативность", "стрессоустойчивость", "обучаемость",
}

RU_TECH_SKILLS: set[str] = {
    "питон", "джанго", "флэск", "фастапи", "докер", "кубернетес",
    "машинное обучение", "глубокое обучение", "нейронные сети",
    "обработка естественного языка", "компьютерное зрение",
    "анализ данных", "визуализация данных", "базы данных",
    "разработка", "программирование", "тестирование", "devops",
    "администрирование", "архитектура", "проектирование",
    "математическая статистика", "математический анализ",
    "теория вероятностей", "эконометрика", "регрессионный анализ",
    "кластерный анализ", "классификация", "прогнозирование",
    "большие данные", "аналитика данных", "бизнес-аналитика",
    "финансовый анализ", "управление проектами", "бухгалтерия",
    "аналитик данных", "аналитик больших данных", "системный аналитик",
    "бизнес аналитик", "продуктовый аналитик", "data analyst",
    "прикладная математика", "информатика", "статистика",
    "визуализация", "дашборды", "отчётность", "моделирование",
}

ALL_SKILLS: set[str] = TECH_SKILLS | SOFT_SKILLS | RU_TECH_SKILLS

EXPERIENCE_LEVELS = {
    "junior": ["junior", "джуниор", "начинающий", "стажёр", "intern", "trainee"],
    "middle": ["middle", "мидл", "mid-level", "специалист"],
    "senior": ["senior", "сениор", "lead", "лид", "ведущий", "главный"],
    "principal": ["principal", "architect", "архитектор", "staff", "head"],
    "manager": ["manager", "менеджер", "руководитель", "директор", "cto", "ceo"],
}
