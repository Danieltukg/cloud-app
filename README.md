# Cloud-Native Deploy Platform

Платформа для деплоя микросервисов в k3s кластер с CI/CD, IaC и мониторингом.

## Что тут есть

- **app/** — простой Flask-сервис с health/ready эндпоинтами
- **terraform/** — инфраструктура в Yandex Cloud (VPC, compute instances)
- **ansible/** — настройка серверов: Docker, пользователи, hardening
- **k8s/** — манифесты: Deployment с rolling update, Service, Ingress, HPA
- **monitoring/** — Prometheus + Node Exporter + Grafana с дашбордами и алертами
- **.gitlab-ci.yml** — пайплайн: lint -> test -> build -> deploy

## Быстрый старт

### 1. Инфраструктура

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# заполнить terraform.tfvars своими данными
terraform init
terraform plan
terraform apply
```

### 2. Настройка серверов

```bash
cd ansible
# прописать IP из terraform output в inventory/hosts.yml
ansible-playbook playbooks/site.yml
```

### 3. k3s кластер

```bash
# на мастере
bash scripts/setup-k3s.sh
# на воркерах выполнить команду из вывода скрипта
```

### 4. Деплой приложения

```bash
cd scripts
bash deploy.sh
```

### 5. Мониторинг

```bash
cd monitoring
docker compose -f docker-compose.monitoring.yml up -d
```

Grafana будет на порту 3000 (admin/changeme), Prometheus на 9090.

## CI/CD

Пайплайн в GitLab CI автоматически:
1. Проверяет код линтером
2. Гоняет тесты
3. Собирает Docker-образ и пушит в registry
4. Деплоит в кластер с rolling update

Нужно настроить переменные в GitLab CI/CD Settings:
- `KUBECONFIG_DATA` — base64 от kubeconfig
