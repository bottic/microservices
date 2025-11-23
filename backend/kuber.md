```sh
Сначала создаешь yaml файлы, потом делаешь по примеру
docker build -t gateway:v1 backend/gateway 
docker build -t auth:v1 backend/auth 
....
После создания образов запускаешь:
kubectl apply -f kuber/k8n/namespace.yaml
kubectl apply -f kuber/k8n/postgres-secret.yaml -f kuber/k8n/postgres.yaml
....
minikube start --driver=docker
minikube image load auth:v1 gateway:v1

Проверить поды:
kubectl get pods -n microservices
Удалить поды:
kubectl delete job auth-migrations -n microservices 
Посмотреть логи:
kubectl logs job/auth-migrations -n microservices
Обновить поды:
kubectl set image deploy/auth auth=auth:v1 -n microservices
kubectl set image deploy/gateway gateway=gateway:v1 -n microservices

Запуск в мир(проброс gateway на localhost:8000):
kubectl port-forward svc/gateway 8000:8000 -n microservices
```

```sh
Обновление образов после правок кода:
Удаляешь kubectl delete namespace microservices Или после пересборки просто обновить образы:
kubectl set image deploy/auth auth=auth:v1 -n microservices
kubectl set image deploy/gateway gateway=gateway:v1 -n microservices
kubectl delete job auth-migrations -n microservices
kubectl apply -f kuber/k8n/alembic-job.yaml

Пересобираешь образы
Запускаешь minikube image load ...
Запускаешь заново все yaml файлы
```