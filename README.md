# Cloud-Native Deploy Platform

Платформа для деплоя микросервисов в k3s кластер с CI/CD, IaC и мониторингом.

## Приложение — VERTEX

Интерактивный атлас горных вершин мира: Flask + PostgreSQL + JS фронтенд.
API для CRUD вершин, фильтрация, поиск, статистика.

## Что тут есть

- **app/** — Flask-бэкенд + статический фронт, PostgreSQL, Dockerfile
- **terraform/** — инфраструктура в Yandex Cloud (VPC, compute instances)
- **ansible/** — настройка серверов: Docker, пользователи, hardening
- **k8s/** — Deployment (app + postgres), Service, Ingress, HPA, Secrets
- **monitoring/** — Prometheus + Node Exporter + Grafana с дашбордами и алертами
- **.gitlab-ci.yml** — пайплайн: lint -> test -> build -> deploy

## Быстрый старт

### Локально (без инфраструктуры)

```bash
cd app
pip install -r requirements.txt
python app.py
```
Откроется на http://localhost:5000 с SQLite базой и начальными данными.

### Полный деплой

### 1. Инфраструктура

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

### 2. Настройка серверов

```bash
cd ansible
ansible-playbook playbooks/site.yml
```

### 3. k3s кластер

```bash
bash scripts/setup-k3s.sh
```

### 4. Деплой приложения

```bash
cp k8s/secrets.yml.example k8s/secrets.yml
# поменяй пароли в secrets.yml
kubectl apply -f k8s/secrets.yml
bash scripts/deploy.sh
```

### 5. Мониторинг

```bash
cd monitoring
docker compose -f docker-compose.monitoring.yml up -d
```

Grafana на порту 3000 (admin/changeme), Prometheus на 9090.

## CI/CD

Пайплайн в GitLab CI автоматически:
1. Проверяет код линтером
2. Гоняет тесты
3. Собирает Docker-образ и пушит в registry
4. Деплоит в кластер с rolling update

Нужно настроить переменные в GitLab CI/CD Settings:
- `KUBECONFIG_DATA` — base64 от kubeconfig
