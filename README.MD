# Перед началом работы создайте фалый:
- auth-config.yaml
- gateway-config.yaml
- postgres-secret.yaml
## auth-config.yaml
Пример заполнения   

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: auth-config
  namespace: microservices
data:
  DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/dbName
  JWT_SECRET: dev-secret
  JWT_ALGORITHM: HS256
  ACCESS_TOKEN_EXPIRES: "15"
  REFRESH_TOKEN_EXPIRES_DAYS: "30"
```
## gateway-config.yaml
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: gateway-config
  namespace: microservices
data:
  AUTH_SERVICE_URL: http://auth:8000
  CATALOG_SERVICE_URL: http://catalog:8000
  JWT_SECRET: dev-secret
  JWT_ALGORITHM: HS256
  # CORS_ORIGINS: http://localhost:5173
  CORS_ORIGINS: http://localhost
```
## postgres-secret.yaml
```
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: microservices
type: Opaque
stringData:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  POSTGRES_DB: dbName

```
# Заполните файлы 
- auth/.env
- gateway/.env

# Старт
Для перезапуска можно использовать restart.sh (нужны sudo права)
```sh
sh restart.sh
```
После выполнения файла запускаем
```bash
kubectl port-forward svc/gateway 8000:8000 -n microservices --address 0.0.0.0
``` 