.PHONY: help start login build push up down logs reset-db

IMAGE    := meimeitou/life-assistant:latest
PLATFORM := linux/amd64
DOCKER   := $(shell command -v docker 2>/dev/null || echo podman)

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  start     检查微信登录状态，启动 nanobot gateway"
	@echo "  login     微信扫码登录"
	@echo "  build     构建 Docker 镜像 (meimeitou/life-assistant:latest)"
	@echo "  push      推送镜像到 Docker Hub"
	@echo "  up        Docker 后台启动"
	@echo "  down      Docker 停止"
	@echo "  logs      查看 Docker 日志"
	@echo "  reset-db  重建数据库（清空所有数据）"

start:
	./start.sh start

login:
	./start.sh login

build:
	$(DOCKER) build --platform $(PLATFORM) -t $(IMAGE) .

push:
	$(DOCKER) push $(IMAGE)

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

reset-db:
	./scripts/reset-db.sh
